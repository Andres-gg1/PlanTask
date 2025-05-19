from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest, HTTPNotFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project
from plantask.models.activity_log import ActivityLog
from plantask.auth.verifysession import verify_session
from plantask.models.task import Task, TasksFile
from plantask.models.microtask import Microtask
from datetime import date

@view_config(route_name='create_task', renderer='plantask:templates/create_task.jinja2', request_method='GET', permission="admin")
@verify_session
def create_task_page(request):
    project_id = request.matchdict.get('project_id')
    project = request.dbsession.query(Project).get(project_id)
    if not project:
        return HTTPFound(location=request.route_url('my_projects')) 
    
    return {
        'project': project,
        'current_date': date.today().isoformat()
    }


@view_config(route_name='create_task', renderer='plantask:templates/create_task.jinja2', request_method='POST', permission="admin")
@verify_session
def create_task(request):
    project_id = request.matchdict.get('project_id')
    project = request.dbsession.query(Project).get(project_id)
    if not project:
        return HTTPFound(location=request.route_url('my_projects')) 

    task_name = request.params.get('name')
    task_description = request.params.get('description')
    due_date = request.params.get('due_date')

    if not task_name or not task_description or not due_date:       #check if all field are complete
        return {
            'project': project,
            'current_date': date.today().isoformat(),
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
                        changes = f"{new_task.__repr__()}"
        )
        request.dbsession.add(activity_log_task_created)
        request.dbsession.flush()

        return HTTPFound(location=request.route_url('project_by_id', id=project.id))

    except SQLAlchemyError as e:
        request.dbsession.rollback()
        return {
            'project': project,
            'current_date': date.today().isoformat(),
            'error_ping': 'An error occurred while creating the task. Please try again.'
        }


@view_config(route_name='task_by_id', renderer='plantask:templates/task.jinja2', request_method='GET')
@verify_session
def task_by_id(request):
    try:
        task_id = int(request.matchdict.get('id'))
        task = request.dbsession.query(Task).filter_by(id=task_id).first()
        if not task:
            return HTTPNotFound("Task not found")
        project = request.dbsession.query(Project).filter_by(id=task.project_id).first()
        microtasks = request.dbsession.query(Microtask).filter_by(task_id=task.id, active=True).all()  # Query microtasks
        tasks_files = request.dbsession.query(TasksFile).filter_by(tasks_id=task.id).all()
        files = [tf.files for tf in tasks_files]

        return {
            'task': task,
            'project': project,
            'microtasks': microtasks,
            'files': files,
            'current_date': date.today().isoformat()
        }
    except Exception:
        return HTTPNotFound("Task not found")
    

@view_config(route_name='edit_task', request_method='POST', permission="admin")
@verify_session
def edit_task(request):
    try:
        task_id = int(request.matchdict.get('id'))
        task = request.dbsession.query(Task).filter_by(id=task_id).first()
        if not task:
            return HTTPNotFound("Task not found")

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
                changes=f"old: {old_title} --> new: {name}"
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
                changes=f"old: {old_description} --> new: {description}"
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
                changes=f"old: {old_due_date.strftime('%Y-%m-%d')} --> new: {new_due_date.strftime('%Y-%m-%d')}"
            )
            request.dbsession.add(activity_log_due_date_changed)

        request.dbsession.flush()

        return HTTPFound(location=request.route_url('task_by_id', id=task.id))
    except Exception as e:
        request.dbsession.rollback()
        return HTTPBadRequest(f"Error editing task: {str(e)}")

@view_config(route_name='delete_task', request_method='POST', permission="admin")
@verify_session
def delete_task(request):
    try:
        task_id = int(request.matchdict.get('id'))
        task = request.dbsession.query(Task).filter_by(id=task_id).first()
        if not task:
            return HTTPNotFound("Task not found")
        project_id = task.project_id

        if task.active:    
            task.active = False
            activity_log_deleted_task = ActivityLog(
                user_id=request.session['user_id'],
                project_id=task.project_id,
                task_id = task.id,
                timestamp=datetime.now(),
                action='task_removed',
                changes=f"task.__repr__()"
            )
            request.dbsession.add(activity_log_deleted_task)
            request.dbsession.flush()
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))
    except Exception as e:
        request.dbsession.rollback()
        return HTTPBadRequest(f"Error deleting task: {str(e)}")