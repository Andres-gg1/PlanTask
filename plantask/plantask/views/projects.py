from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project, ProjectsUser
from plantask.models.user import User
from plantask.auth.verifysession import verify_session
from sqlalchemy import and_, select
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from plantask.models.user import User
from plantask.models.project import ProjectsUser
from urllib.parse import urlencode

@view_config(route_name='my_projects', renderer='/templates/my_projects.jinja2', request_method='GET')
@verify_session
def my_projects_page(request):
    projects = request.dbsession.query(Project)\
        .join(ProjectsUser, Project.id == ProjectsUser.project_id)\
        .filter(ProjectsUser.user_id == request.session.get('user_id'))\
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

        new_project = Project(
            name=name,
            description=description,
            creation_datetime=datetime.now()
        )

        request.dbsession.add(new_project)
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
        project = request.dbsession.query(Project).filter_by(id=project_id).first()

        projects_user = request.dbsession.query(ProjectsUser).filter(
            and_(
                ProjectsUser.project_id == project_id,
                ProjectsUser.user_id == request.session.get('user_id')
            )
        ).first()

        if not project or not projects_user:
            return {"error_ping": "You don't have access to this project."}

        project_members = request.dbsession.query(User, ProjectsUser.role).join(ProjectsUser).filter(
            ProjectsUser.project_id == project_id).all()

        role_map = {
            'admin': 'Administrator',
            'project_manager': 'Project Manager',
            'member': 'Member',
            'observer': 'Observer'
        }

        mapped_members = [(member, role_map.get(role, role)) for member, role in project_members]

        role = projects_user.role
        announcement = request.params.get('announcement')
        message = request.params.get('message')
        return {
            "project": project,
            "project_members": mapped_members, 
            "show_role": role,
            "announcement": announcement,
            "message": message 
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

    project.name = request.POST.get('name', project.name)
    project.description = request.POST.get('description', project.description)
    request.dbsession.flush()
    return HTTPFound(location=request.route_url('project_by_id', id=project_id))

@view_config(route_name='delete_project', request_method='GET', permission="admin")
@verify_session
def delete_project(request):
    project_id = int(request.matchdict['id'])
    project = request.dbsession.query(Project).filter_by(id=project_id).first()
    if not project:
        return HTTPNotFound()

    request.dbsession.query(ProjectsUser).filter_by(project_id=project_id).delete()
    request.dbsession.delete(project)
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
            member_subquery = select(ProjectsUser.user_id).where(
                ProjectsUser.project_id == project_id
            )

            query = query.filter(~User.id.in_(member_subquery))

        
        users = query.limit(10).all()
        
        # Return found users
        result = [{
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
        } for user in users]
        return result

    
    except SQLAlchemyError as e:
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
        
        # Verify if user has permissions to add members
        user_relation = request.dbsession.query(ProjectsUser).filter(
            and_(
                ProjectsUser.project_id == project_id,
                ProjectsUser.user_id == request.session.get('user_id'),
                ProjectsUser.role.in_(['admin', 'project_manager'])
            )
        ).first()
        
        if not user_relation:
            return HTTPFound(location=request.route_url('invalid_permissions'))
        
        user_ids = request.POST.getall('user_ids')
        
        if user_ids:
            for user_id in user_ids:
                try:
                    user_id = int(user_id)
                    
                    # Check if user is already in the project
                    existing_relation = request.dbsession.query(ProjectsUser).filter(
                        and_(
                            ProjectsUser.project_id == project_id,
                            ProjectsUser.user_id == user_id
                        )
                    ).first()
                    
                    # Only add if user is not already in the project
                    if not existing_relation:
                        user = request.dbsession.query(User).filter_by(id=user_id).first()
                        if user:
                            project_user = ProjectsUser(
                                project_id=project_id, 
                                user_id=user_id, 
                                role="member"
                            )
                            request.dbsession.add(project_user)
                except ValueError:
                    continue
            
            request.dbsession.flush()
        
        query_string = urlencode({"announcement": "success", "message": "Members added successfully."})
        url = f"{request.route_url('project_by_id', id=project_id)}?{query_string}"
        return HTTPFound(location=url)
        
    except SQLAlchemyError as e:
        request.dbsession.rollback()
        return {"error_ping": f"Error adding members to project: {str(e)}"}
    except Exception as e:
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))
    
@view_config(route_name='remove_member', request_method='POST', permission='admin')
@verify_session
def remove_member(request):
    try:
        project_id = int(request.matchdict['id'])
        user_id = int(request.POST.get('user_id'))

        # Asegurarse de que no se elimine a sí mismo
        if user_id == request.session.get('user_id'):
            return HTTPFound(location=request.route_url('project_by_id', id=project_id))

        # Verificar que el usuario pertenece al proyecto
        relation = request.dbsession.query(ProjectsUser).filter_by(
            project_id=project_id, user_id=user_id
        ).first()

        if relation:
            request.dbsession.delete(relation)
            request.dbsession.flush()

        query_string = urlencode({"announcement": "alert", "message": "Members removed from the project successfully."})
        url = f"{request.route_url('project_by_id', id=project_id)}?{query_string}"
        return HTTPFound(location=url)

    except Exception:
        request.dbsession.rollback()
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))
