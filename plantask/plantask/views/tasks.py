from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest, HTTPNotFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project, ProjectsUser
from plantask.models.activity_log import ActivityLog
from plantask.auth.verifysession import verify_session
from plantask.models.task import Task, TasksFile, TaskComment
from plantask.models.label import Label, LabelsTask
from plantask.models.microtask import Microtask, MicrotaskComment
from plantask.models.file import File
from datetime import datetime, date
from sqlalchemy import and_

@view_config(route_name='create_task', renderer='plantask:templates/create_item.jinja2', request_method='GET', permission="admin")
@verify_session
def create_task_page(request):
    project_id = request.matchdict.get('project_id')

    project = request.dbsession.query(Project).get(project_id)
    if not project:
        raise HTTPNotFound()

    
    form_config = {
        'title': 'Create New Task',
        'subtitle': f'For project: {project.name}',
        'icon': 'bi bi-file-post',
        'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'accent_color': '#667eea',
        'name_label': 'Task Name',
        'name_placeholder': 'Enter a descriptive task name...',
        'description_placeholder': 'Describe what needs to be accomplished...',
        'button_text': 'Create Task',
        'action': request.route_url('create_task', project_id=project.id),
        'show_date': True,
        'max_date': None
    }
    
    return {
        'project': project,
        'current_date': date.today().isoformat(),
        'form_config': form_config
    }


@view_config(route_name='create_task', renderer='plantask:templates/create_item.jinja2', request_method='POST', permission="admin")
@verify_session
def create_task(request):
    project_id = request.matchdict.get('project_id')
    
    project = request.dbsession.query(Project).get(project_id)
    if not project:
        raise HTTPNotFound()

    task_name = request.params.get('name')
    task_description = request.params.get('description')
    due_date = request.params.get('due_date')

    form_config = {
        'title': 'Create New Task',
        'subtitle': f'For project: {project.name}',
        'icon': 'bi bi-list-check',
        'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'accent_color': '#667eea',
        'name_label': 'Task Name',
        'name_placeholder': 'Enter a descriptive task name...',
        'description_placeholder': 'Describe what needs to be accomplished...',
        'button_text': 'Create Task',
        'action': request.route_url('create_task', project_id=project.id),
        'show_date': True,
        'max_date': None
    }

    if not task_name or not task_description or not due_date:       #check if all field are complete
        return {
            'project': project,
            'current_date': date.today().isoformat(),
            'form_config': form_config,
            'error_ping': 'All fields are required.'
        }

    try:
        new_task = Task(                                            #instanciate new task
            project_id=project.id,
            task_title=task_name,
            task_description=task_description,
            percentage_complete=0.0,
            date_created=datetime.now(),
            due_date=datetime.strptime(due_date, '%Y-%m-%d'),
            status='assigned'
        )
        request.dbsession.add(new_task)
        request.dbsession.flush()
        

        activity_log_task_created = ActivityLog(
                        user_id = request.session['user_id'],
                        project_id = project.id,
                        task_id = new_task.id,
                        timestamp = datetime.now(),
                        action = 'task_created',
                        changes = f"{new_task.task_title}"
        )
        request.dbsession.add(activity_log_task_created)
        request.dbsession.flush()

        return HTTPFound(location=request.route_url('project_by_id', id=project.id))

    except SQLAlchemyError as e:
        request.dbsession.rollback()
        return {
            'project': project,
            'current_date': date.today().isoformat(),
            'form_config': form_config,
            'error_ping': 'An error occurred while creating the task. Please try again.'
        }


@view_config(route_name='task_by_id', renderer='plantask:templates/task.jinja2', request_method='GET')
@verify_session
def task_by_id(request):
    try:
        task_id = int(request.matchdict.get('id'))
        user_id = request.session.get('user_id')
        
        task = request.dbsession.query(Task).filter_by(id=task_id).first()
        if not task:
            raise HTTPNotFound()
            
        # Check if user is a member of the project
        current_user_assoc = (
            request.dbsession.query(ProjectsUser)
            .filter(
                ProjectsUser.project_id == task.project_id,
                ProjectsUser.user_id == user_id,
                ProjectsUser.active == True
            )
            .first()
        )

        if not current_user_assoc:
            return HTTPFound(location=request.route_url('invalid_permissions'))
            
        project = request.dbsession.query(Project).filter_by(id=task.project_id).first()
        microtasks = request.dbsession.query(Microtask).filter_by(task_id=task.id, active=True).all()
        tasks_files = request.dbsession.query(TasksFile).filter_by(tasks_id=task.id).all()
        files = [tf.files for tf in tasks_files]

        assigned_labels = (
            request.dbsession.query(Label.id, Label.label_name, Label.label_hex_color)
            .join(LabelsTask, LabelsTask.labels_id == Label.id)
            .filter(LabelsTask.tasks_id == task.id)
            .all()
        )
        assigned_label_ids = [label[0] for label in assigned_labels]

        all_project_labels = (
            request.dbsession.query(Label.id, Label.label_name, Label.label_hex_color)
            .filter_by(project_id=project.id)
            .order_by(Label.label_name.asc())
            .all()
        )

        unassigned_labels = [label for label in all_project_labels if label[0] not in assigned_label_ids]

        project_labels_ordered = assigned_labels + unassigned_labels

        return {
            'task': task,
            'project': project,
            'microtasks': microtasks,
            'files': files,
            'current_date': date.today().isoformat(),
            'labels': assigned_labels,
            'project_labels': project_labels_ordered,
            'assigned_label_ids': assigned_label_ids,
            'task_id': task_id
        }
    except Exception:
        return HTTPFound(location=request.route_url('invalid_permissions'))

    

@view_config(route_name='edit_task', request_method='POST', permission="admin")
@verify_session
def edit_task(request):
    try:
        task_id = int(request.matchdict.get('id'))
        user_id = request.session.get('user_id')
        
        task = request.dbsession.query(Task).filter_by(id=task_id).first()
        if not task:
            raise HTTPNotFound()

        # Check if user is a member of the project
        current_user_assoc = (
            request.dbsession.query(ProjectsUser)
            .filter(
                ProjectsUser.project_id == task.project_id,
                ProjectsUser.user_id == user_id,
                ProjectsUser.active == True
            )
            .first()
        )

        if not current_user_assoc:
            return HTTPFound(location=request.route_url('invalid_permissions'))

        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        due_date = request.POST.get('due_date', '').strip()

        if not name or not description or not due_date:
            project = request.dbsession.query(Project).filter_by(id=task.project_id).first()
            return {
                'task': task,
                'project': project,
                'error_ping': 'All fields are required.'
            }

        # Log changes to task title
        if task.task_title != name:
            old_title = task.task_title
            task.task_title = name
            activity_log_title_changed = ActivityLog(
                user_id=request.session['user_id'],
                task_id=task.id,
                project_id=task.project_id,
                timestamp=datetime.now(),
                action='task_edited_title',
                changes=f"{old_title}, {name}"
            )
            request.dbsession.add(activity_log_title_changed)

        # Log changes to task description
        if task.task_description != description:
            old_description = task.task_description
            task.task_description = description
            activity_log_description_changed = ActivityLog(
                user_id=request.session['user_id'],
                task_id=task.id,
                project_id=task.project_id,
                timestamp=datetime.now(),
                action='task_edited_description',
                changes=f"{old_description}, {description}"
            )
            request.dbsession.add(activity_log_description_changed)

        # Log changes to task due date
        new_due_date = datetime.strptime(due_date, '%Y-%m-%d')
        if task.due_date != new_due_date:
            old_due_date = task.due_date
            task.due_date = new_due_date
            activity_log_due_date_changed = ActivityLog(
                user_id=request.session['user_id'],
                task_id=task.id,
                project_id=task.project_id,
                timestamp=datetime.now(),
                action='task_edited_duedate',
                changes=f"{old_due_date.strftime('%Y-%m-%d')}, {new_due_date.strftime('%Y-%m-%d')}"
            )
            request.dbsession.add(activity_log_due_date_changed)

        request.dbsession.flush()

        return HTTPFound(location=request.route_url('task_by_id', id=task.id))
    except Exception as e:
        request.dbsession.rollback()
        return HTTPFound(location=request.route_url('invalid_permissions'))

@view_config(route_name='delete_task', request_method='POST', permission="admin")
@verify_session
def delete_task(request):
    try:
        task_id = int(request.matchdict.get('id'))
        user_id = request.session.get('user_id')
        
        task = request.dbsession.query(Task).filter_by(id=task_id).first()
        if not task:
            raise HTTPNotFound()

        # Check if user is a member of the project
        current_user_assoc = (
            request.dbsession.query(ProjectsUser)
            .filter(
                ProjectsUser.project_id == task.project_id,
                ProjectsUser.user_id == user_id,
                ProjectsUser.active == True
            )
            .first()
        )

        if not current_user_assoc:
            return HTTPFound(location=request.route_url('invalid_permissions'))
            
        project_id = task.project_id

        if task.active:    
            task.active = False
            activity_log_deleted_task = ActivityLog(
                user_id=request.session['user_id'],
                project_id=task.project_id,
                task_id = task.id,
                timestamp=datetime.now(),
                action='task_removed',
                changes=f"{task.task_title}"
            )
            request.dbsession.add(activity_log_deleted_task)
            request.dbsession.flush()
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))
    except Exception as e:
        request.dbsession.rollback()
        return HTTPFound(location=request.route_url('invalid_permissions'))


@view_config(route_name='add_label', request_method='POST', permission="admin", require_csrf = True)
@verify_session
def add_label(request):
    try:
        project_id = int(request.matchdict.get('project_id'))
        hex_color = str(request.POST.get('label_color'))
        label_name = str(request.POST.get('label_name'))
        relation = bool(request.POST.get('relation'))
        project = request.dbsession.query(Project).filter_by(id = project_id).first()
        if not project:
            raise HTTPNotFound("Project not found")
       
        label = Label(project_id = project_id, label_name = label_name, label_hex_color = hex_color)
        request.dbsession.add(label)
        label_added_log = ActivityLog(
            user_id=request.session['user_id'],
            project_id=project_id,
            timestamp=datetime.now(),
            action='project_added_label',
            changes=f"{label.label_name}",
        )
        request.dbsession.add(label_added_log)
        request.dbsession.flush()
        if relation:
            task_id = int(request.POST.get('task_id'))
            labels_task = LabelsTask(
                labels_id=label.id,
                tasks_id=task_id
            )
            request.dbsession.add(labels_task)
            request.dbsession.flush()
            return HTTPFound(location=request.route_url('task_by_id', id = task_id))
        return HTTPFound(location=request.route_url('project_by_id', id = project_id))
 
    except Exception as e:
        request.dbsession.rollback()
        return HTTPBadRequest(f"Error adding label: {str(e)}")
 
 
@view_config(route_name='assign_label_to_task', request_method='POST', permission="admin")
@verify_session
def assign_label(request):
    try:
        task_id = int(request.matchdict.get('id'))
        task = request.dbsession.query(Task).filter_by(id=task_id).first()
        if not task:
            raise HTTPNotFound("Task not found")
        
        label_id = request.POST.get('label_id')
        if not label_id:
            return HTTPBadRequest("Label ID is required")
 
        labels_task = LabelsTask(
            labels_id=label_id,
            tasks_id=task.id
        )
        request.dbsession.add(labels_task)
        request.dbsession.flush()
 
        return HTTPFound(location=request.route_url('task_by_id', id=task.id))
    except Exception as e:
        request.dbsession.rollback()
        return HTTPBadRequest(f"Error adding label: {str(e)}")
    
    
@view_config(route_name='toggle_label_for_task', request_method='POST', permission="admin")
@verify_session
def toggle_label_for_task(request):
    try:
        task_id = int(request.matchdict.get('id'))
        label_id = int(request.POST.get('label_id'))
        labels_task = request.dbsession.query(LabelsTask).filter_by(labels_id=label_id, tasks_id=task_id).first()
        if labels_task:
            request.dbsession.delete(labels_task)

            label = request.dbsession.query(Label).filter_by(id = label_id).first()

            log_removed_label_task = ActivityLog(
                user_id=request.session['user_id'],
                task_id = task_id,
                project_id = label.project_id,
                timestamp=datetime.now(),
                action='project_task_removed_label',
                changes=f"{label.label_name}"
            )
            request.dbsession.add(log_removed_label_task)

            request.dbsession.flush()
            return Response('unassigned', status=200)
        else:
            new_labels_task = LabelsTask(labels_id=label_id, tasks_id=task_id)
            request.dbsession.add(new_labels_task)
            
            label = request.dbsession.query(Label).filter_by(id = label_id).first()

            log_assigned_label_task = ActivityLog(
                user_id=request.session['user_id'],
                task_id = task_id,
                project_id = label.project_id,
                timestamp=datetime.now(),
                action='project_task_assigned_label',
                changes=f"{label.label_name}"
            )
            request.dbsession.add(log_assigned_label_task)
            
            request.dbsession.flush()
            return Response('assigned', status=200)
    except Exception as e:
        request.dbsession.rollback()
        return HTTPBadRequest(f"Error toggling label: {str(e)}")
    
@view_config(route_name='edit_label', request_method='POST', permission="admin", require_csrf=True)
@verify_session
def edit_label(request):
    try:
        label_id = int(request.matchdict.get('label_id'))
        label_name = str(request.POST.get('label_name'))
        hex_color = str(request.POST.get('label_color'))
        
        label = request.dbsession.query(Label).filter_by(id=label_id).first()
        if not label:
            raise HTTPNotFound("Label not found")

        label.label_name = label_name
        label.label_hex_color = hex_color
        request.dbsession.flush()

        # Redirect back to project or task page after editing
        project_id = label.project_id
        task_id = request.POST.get('task_id')
        if task_id:
            return HTTPFound(location=request.route_url('task_by_id', id=int(task_id)))
        else:
            return HTTPFound(location=request.route_url('project_by_id', id=project_id))

    except Exception as e:
        request.dbsession.rollback()
        return HTTPBadRequest(f"Error editing label: {str(e)}")

@view_config(route_name="update_microtask_status", request_method="POST", renderer="json")
@verify_session
def update_microtask_status(request):
    try:
        data = request.json_body
        microtask_id = int(data['microtask_id'])
        new_status = data['new_status']

        microtask = request.dbsession.query(Microtask).filter_by(id=microtask_id).first()
        if not microtask:
            return {"error": "Microtask not found"}

        previous_status = microtask.status
        if previous_status == new_status:
            return {"message": "No status change"}
        microtask.status = new_status

        log_updated_microtask_status = ActivityLog(
                user_id=request.session['user_id'],
                project_id = microtask.task.project_id,
                task_id = microtask.task_id,
                microtask_id = microtask.id,
                timestamp=datetime.now(),
                action='microtask_edited_status',
                changes=f"{microtask.status}"
            )
        request.dbsession.add(log_updated_microtask_status)

        request.dbsession.flush()

        return {"message": "Status updated"}
    except Exception as e:
        return {"error": str(e)}

@view_config(route_name="add_microtask_comment", request_method="POST", renderer="json")
@verify_session
def add_microtask_comment(request):
    try:
        # Get data from JSON body instead of POST
        microtask_id = int(request.matchdict.get('microtask_id'))
        data = request.json_body
        content = data.get('content')

        if not content:
            return {"error": "Comment content cannot be empty"}

        microtask = request.dbsession.query(Microtask).filter_by(id=microtask_id).first()
        if not microtask:
            return {"error": "Microtask not found"}

        new_comment = MicrotaskComment(
            user_id=request.session['user_id'],
            microtask_id=microtask_id,
            time_posted=datetime.now(),
            content=content
        )
        request.dbsession.add(new_comment)

        microtask_comment_added_log = ActivityLog(
            user_id = request.session['user_id'],
            microtask_id = microtask.id,
            task_id = microtask.task_id,
            project_id = microtask.task.project_id,
            timestamp = datetime.now(),
            action = "microtask_added_comment",
            changes = content
        )
        request.dbsession.add(microtask_comment_added_log)        

        request.dbsession.flush()

        # Return the new comment data
        return {
            "message": "Comment added successfully",
            "comment": {
                "id": new_comment.id,
                "user_id": new_comment.user_id,
                "username": request.session.get('username'),
                "time_posted": new_comment.time_posted.strftime('%Y-%m-%d %H:%M:%S'),
                "content": new_comment.content
            }
        }
    except Exception as e:
        request.dbsession.rollback()
        return {"error": str(e)}

@view_config(route_name="get_microtask_comments", request_method="GET", renderer="json")
@verify_session
def get_microtask_comments(request):
    try:
        microtask_id = int(request.params.get('microtask_id'))
        microtask = request.dbsession.query(Microtask).filter_by(id=microtask_id).first()

        if not microtask:
            return {"error": "Microtask not found"}

        comments = []
        for comment in microtask.comments:
            user = comment.user
            profile_picture_url = None
            if user and user.user_image_id:
                file = request.dbsession.query(File).filter_by(id=user.user_image_id).first()
                if file:
                    profile_picture_url = file.route
            username = user.first_name + " " + user.last_name if user else "Unknown"
            comments.append({
                "id": comment.id,
                "user_id": comment.user_id,
                "username": username,
                "profile_picture_url": profile_picture_url,
                "content": comment.content,
                "time_posted": comment.time_posted.strftime('%Y-%m-%d %H:%M:%S')
            })

        return {"comments": comments}
    except Exception as e:
        return {"error": str(e)}
    
@view_config(route_name="add_task_comment", request_method="POST", renderer="json")
@verify_session
def add_task_comment(request):
    try:
        task_id = int(request.matchdict.get('task_id'))
        content = request.POST.get('content')

        if not content:
            return {"error": "Comment content cannot be empty"}

        task = request.dbsession.query(Task).filter_by(id=task_id).first()
        if not task:
            return {"error": "Task not found"}

        new_comment = TaskComment(
            user_id=request.session['user_id'],
            task_id=task_id,
            time_posted=datetime.now(),
            content=content
        )
        request.dbsession.add(new_comment)

        comment_added_log = ActivityLog(
            user_id = request.session['user_id'],
            task_id = task_id,
            project_id = task.project_id,
            timestamp = datetime.now(),
            action = "task_added_comment",
            changes = content
        )
        request.dbsession.add(comment_added_log)

        request.dbsession.flush()
        return {
            "message": "Comment added successfully",
            "comment": {
                "id": new_comment.id,
                "user_id": new_comment.user_id,
                "username": request.session.get('username'),
                "time_posted": new_comment.time_posted.strftime('%Y-%m-%d %H:%M:%S'),
                "content": new_comment.content
            }
        }
    except Exception as e:
        request.dbsession.rollback()
        return {"error": str(e)}
    
@view_config(route_name="get_task_comments", request_method="GET", renderer="json")
@verify_session
def get_task_comments(request):
    try:
        task_id = int(request.params.get('task_id'))
        task_c = request.dbsession.query(TaskComment).filter_by(task_id=task_id).all()
        if not task_c:
            return {"error": "No comments found for this task"}
        comments = []
        for c in task_c:
            user = c.user
            # Get the profile picture URL if available
            profile_picture_url = None
            if user and user.user_image_id:
                file = request.dbsession.query(File).filter_by(id=user.user_image_id).first()
                if file:
                    profile_picture_url = file.route
            username = user.first_name + " " + user.last_name if user else "Unknown"
            comments.append({
                "user_id": c.user_id,
                "username": username,
                "profile_picture_url": profile_picture_url,
                "content": c.content,
                "time_posted": c.time_posted.strftime('%Y-%m-%d %H:%M:%S')
            })
        return {"comments": comments}
    except Exception as e:
        return {"error": str(e)}