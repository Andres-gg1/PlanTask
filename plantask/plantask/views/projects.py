from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPBadRequest, Response
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from sqlalchemy import and_, select
from plantask.models.project import Project, ProjectsUser
from plantask.models.user import User
from plantask.models.activity_log import ActivityLog
from plantask.models.task import Task
from plantask.models.label import Label, LabelsProjectsUser
from plantask.auth.verifysession import verify_session

from plantask.utils.events import UserAddedToProjectEvent, TaskReadyForReviewEvent

import json


@view_config(route_name='my_projects', renderer='/templates/my_projects.jinja2', request_method='GET')
@verify_session
def my_projects_page(request):
    projects = request.dbsession.query(Project)\
        .join(ProjectsUser, Project.id == ProjectsUser.project_id)\
        .filter(ProjectsUser.user_id == request.session.get('user_id'), Project.active == True)\
        .all()
    return {'projects': projects}

@view_config(route_name='create_project', renderer='/templates/create_project.jinja2', request_method='GET', permission="admin")
@verify_session
def create_project_page(request):
    return {}

@view_config(route_name='create_project', renderer='/templates/create_project.jinja2', request_method='POST', permission="admin")
@verify_session
def create_project(request):
    try:
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not name or not description:
            return {"error_ping": "Please provide a name and a description for the project."}

        new_project = Project(name=name, description=description, creation_datetime=datetime.now())
        request.dbsession.add(new_project)
        request.dbsession.flush()
        activity_log_new_project = ActivityLog(
            user_id=request.session['user_id'],
            project_id=new_project.id,  # Added project.id
            timestamp=datetime.now(),
            action='project_added',
            changes=f"{new_project.__repr__()}",
        )
        request.dbsession.add(activity_log_new_project)
        request.dbsession.flush()

        project_creator_relation = ProjectsUser(
            project_id=new_project.id,
            user_id=request.session.get('user_id'),
            role="project_manager"
        )
        request.dbsession.add(project_creator_relation)
        request.dbsession.flush()

        return HTTPFound(location=request.route_url('project_by_id', id=new_project.id))

    except SQLAlchemyError:
        request.dbsession.rollback()
        return {"error_ping": "An error occurred while creating the project. Please try again."}

@view_config(route_name='project_by_id', request_method='GET', renderer='/templates/project.jinja2')
@verify_session
def project_page(request):
    try:
        project_id = int(request.matchdict.get('id'))
        project = request.dbsession.query(Project).filter_by(id=project_id, active=True).first()

        if not project:
            return {"error_ping": "You don't have access to this project or it is inactive."}

        projects_user = request.dbsession.query(ProjectsUser).filter(
            and_(
                ProjectsUser.project_id == project_id,
                ProjectsUser.user_id == request.session.get('user_id')
            )
        ).first()

        if not projects_user:
            return {"error_ping": "You don't have access to this project."}

        project_members = request.dbsession.query(User, ProjectsUser.role)\
            .join(ProjectsUser).filter(ProjectsUser.project_id == project_id).all()

        role_map = {
            'admin': 'Administrator',
            'project_manager': 'Project Manager',
            'member': 'Member',
            'observer': 'Observer'
        }
        mapped_members = [(member, role_map.get(role, role)) for member, role in project_members]

        # Fetch tasks grouped by status
        tasks_by_status = {
            status: request.dbsession.query(Task)
                .filter_by(project_id=project_id, status=status, active = True)
                .order_by(Task.due_date)
                .all()
            for status in ['assigned', 'in_progress', 'under_review', 'completed']
        }
        
        project_labels = (
            request.dbsession.query(Label.id, Label.label_name, Label.label_hex_color).
            filter_by(project_id = project.id).order_by(Label.label_name.asc()).all()
        )
        
        member_labels = {}
        label_assignments = request.dbsession.query(
            ProjectsUser.user_id, 
            LabelsProjectsUser.labels_id
        ).join(
            LabelsProjectsUser, ProjectsUser.id == LabelsProjectsUser.projects_users_id
        ).filter(
            ProjectsUser.project_id == project_id
        ).all()

        for user_id, label_id in label_assignments:
            if user_id not in member_labels:
                member_labels[user_id] = []
            member_labels[user_id].append(label_id)

        flashes = request.session.pop_flash()
        
        return {
            "project": project,
            "project_members": mapped_members,
            "show_role": projects_user.role,
            "flashes": flashes,
            "tasks_by_status": tasks_by_status,
            "project_labels" : project_labels,
            "member_labels": member_labels
        }

    except SQLAlchemyError:
        request.dbsession.rollback()
        return {"error_ping": "An error occurred while fetching the project. Please try again."}

@view_config(route_name='edit_project', request_method='POST', permission="admin")
@verify_session
def edit_project(request):
    project_id = int(request.matchdict['id'])
    project = request.dbsession.query(Project).filter_by(id=project_id).first()
    if not project:
        return HTTPNotFound()

    if project.name != request.POST.get('name', project.name):
        old_name = project.name
        project.name = request.POST.get('name', project.name)
        activity_log_project_name_changed = ActivityLog(
            user_id=request.session['user_id'],
            project_id=project.id,  # Added project.id
            timestamp=datetime.now(),
            action='project_edited_title',
            changes=f"old: {old_name} --> new: {request.POST.get('name', project.name)}"
        )
        request.dbsession.add(activity_log_project_name_changed)
        request.dbsession.flush()

    if project.description != request.POST.get('description', project.description):
        old_description = project.description
        project.description = request.POST.get('description', project.description)
        activity_log_project_description_changed = ActivityLog(
            user_id=request.session['user_id'],
            project_id=project.id,  # Added project.id
            timestamp=datetime.now(),
            action='project_edited_description',
            changes=f"old: {old_description} --> new: {request.POST.get('description', project.description)}"
        )
        request.dbsession.add(activity_log_project_description_changed)
        request.dbsession.flush()

    return HTTPFound(location=request.route_url('project_by_id', id=project_id))

@view_config(route_name='delete_project', request_method='GET', permission="admin")
@verify_session
def delete_project(request):
    project_id = int(request.matchdict['id'])
    project = request.dbsession.query(Project).filter_by(id=project_id).first()
    if not project:
        return HTTPNotFound()

    if project.active:
        project.active = False
        activity_log_removed_project = ActivityLog(
            user_id=request.session['user_id'],
            project_id=project.id,  # Added project.id
            timestamp=datetime.now(),
            action='project_removed',
            changes=f"Project: {project.name} set to inactive"
        )
        request.dbsession.add(activity_log_removed_project)
        request.dbsession.flush()

    return HTTPFound(location=request.route_url('my_projects'))

@view_config(route_name='search_users', renderer='json', request_method='GET', permission="admin")
@verify_session
def search_users(request):
    try:
        username_search = request.GET.get('username', '').strip()
        if not username_search or len(username_search) < 2:
            return []

        project_id = request.GET.get('project_id')
        if project_id:
            try:
                project_id = int(project_id)
            except ValueError:
                project_id = None

        query = request.dbsession.query(User).filter(User.username.ilike(f"%{username_search}%"))

        if project_id:
            member_subquery = select(ProjectsUser.user_id).where(ProjectsUser.project_id == project_id)
            query = query.filter(~User.id.in_(member_subquery))

        users = query.limit(10).all()
        return [{
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
        } for user in users]

    except SQLAlchemyError:
        request.dbsession.rollback()
        return []

@view_config(route_name='add_member', request_method='POST', permission="admin")
@verify_session
def add_member(request):
    try:
        project_id = int(request.matchdict['id'])
        project = request.dbsession.query(Project).filter_by(id=project_id).first()
        if not project:
            return HTTPNotFound()

        user_ids = request.POST.getall('user_ids')
        if user_ids:
            for user_id in user_ids:
                try:
                    user_id = int(user_id)
                    existing_relation = request.dbsession.query(ProjectsUser).filter(
                        and_(
                            ProjectsUser.project_id == project_id,
                            ProjectsUser.user_id == user_id
                        )
                    ).first()
                    if not existing_relation:
                        user = request.dbsession.query(User).filter_by(id=user_id).first()
                        role = request.POST.get('role')
                        if user:
                            project_user = ProjectsUser(
                                project_id=project_id,
                                user_id=user_id,
                                role=str(role)
                            )
                            activity_log_added_user = ActivityLog(
                                user_id=request.session['user_id'],
                                project_id=project.id,
                                object_user_id=user.id,
                                timestamp=datetime.now(),
                                action='project_added_user',
                                changes=f"User: {user.username} added to Project: {project.name}"
                            )
                            request.dbsession.add(project_user)
                            request.dbsession.add(activity_log_added_user)
                            request.dbsession.flush()

                            event = UserAddedToProjectEvent(request, project_id=project_id, user_id = user_id)
                            request.registry.notify(event)


                except ValueError:
                    continue
            request.dbsession.flush()

        request.session.flash({'message': 'Members added successfully.', 'style': 'success'})
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))

    except SQLAlchemyError as e:
        request.dbsession.rollback()
        return {"error_ping": f"Error adding members to project: {str(e)}"}
    except Exception:
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))
    
@view_config(route_name='edit_member', request_method='POST', permission='admin')
@verify_session
def edit_member(request):
    try:
        project_id = int(request.matchdict['id'])
        project = request.dbsession.query(Project).filter_by(id=project_id).first()
        if not project:
            return HTTPNotFound()

        user_id = int(request.POST.get('user_id'))
        new_role = request.POST.get('role')
        label_ids = request.POST.getall('labels')  # IDs from form

        # Get the ProjectsUser row (relationship between user & project)
        project_user = request.dbsession.query(ProjectsUser).filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()

        if not project_user:
            request.session.flash({'message': 'User not found in project.', 'style': 'danger'})
            return HTTPFound(location=request.route_url('project_by_id', id=project_id))

        # Update role if changed
        if project_user.role != new_role:
            project_user.role = new_role
            request.dbsession.flush()

        # Delete all previous label associations
        request.dbsession.query(LabelsProjectsUser).filter_by(
            projects_users_id=project_user.id
        ).delete()

        # Add updated labels
        for label_id in label_ids:
            try:
                label_link = LabelsProjectsUser(
                    labels_id=label_id,
                    projects_users_id=project_user.id
                )
                request.dbsession.add(label_link)
            except ValueError:
                continue

        request.dbsession.flush()

        request.session.flash({'message': 'Member updated successfully.', 'style': 'success'})
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))

    except SQLAlchemyError as e:
        request.dbsession.rollback()
        return {"error_ping": f"Error editing member: {str(e)}"}
    except Exception:
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))

@view_config(route_name='remove_member', request_method='POST', permission='admin')
@verify_session
def remove_member(request):
    try:
        project_id = int(request.matchdict['id'])
        user_id = int(request.POST.get('user_id'))

        project = request.dbsession.query(Project).filter_by(id=project_id).first()
        if not project:
            return HTTPNotFound()

        relation = request.dbsession.query(ProjectsUser).filter_by(
            project_id=project_id, user_id=user_id
        ).first()

        if relation:
            request.dbsession.delete(relation)
            activity_log_removed_user = ActivityLog(
                user_id=request.session['user_id'],
                project_id=project.id,  # Added project.id
                object_user_id=user_id,
                timestamp=datetime.now(),
                action='project_removed_user',
                changes=f"User removed from Project: {project.name}"
            )
            request.dbsession.add(activity_log_removed_user)
            request.dbsession.flush()

        request.session.flash({'message': 'Member removed successfully.', 'style': 'warning'})
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))

    except SQLAlchemyError as e:
        request.dbsession.rollback()
        return {"error_ping": f"Error removing member from project: {str(e)}"}
    except Exception:
        request.dbsession.rollback()
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))
    


@view_config(route_name='update_task_status', request_method='POST', renderer='json')
@verify_session
def update_task_status(request):
    try:
        data = request.json_body
        task_id = int(data['task_id'])
        new_status = data['new_status']

        task = request.dbsession.query(Task).filter_by(id=task_id).first()
        if not task:
            return {"error": "Task not found"}

        prevous_status = task.status
        if prevous_status == new_status:
            return {"message": "No status change"}
        task.status = new_status
        request.dbsession.flush()

        if new_status == 'under_review' and prevous_status != 'under_review':  
            request.registry.notify(TaskReadyForReviewEvent(request, task_id))
        return {"message": "Status updated"}
    except Exception as e:
        return {"error": str(e)}
    
    
@view_config(route_name='kanban_partial', renderer='plantask:templates/kanban.jinja2', request_method='GET')
@verify_session
def kanban_partial(request):
    project_id = int(request.matchdict.get('id'))
    project = request.dbsession.query(Project).filter_by(id=project_id).first()
    if not project:
        return Response('Project not found', status=404)
    
    tasks_by_status = {
        status: request.dbsession.query(Task)
            .filter_by(project_id=project_id, status=status, active = True)
            .order_by(Task.due_date)
            .all()
        for status in ['assigned', 'in_progress', 'under_review', 'completed']
    }
    return {
        "project": project,
        "tasks_by_status": tasks_by_status
    }