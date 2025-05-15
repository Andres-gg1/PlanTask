from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest, HTTPNotFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project
from plantask.auth.verifysession import verify_session
from plantask.models.task import Task
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

    if not task_name or not task_description or not due_date:
        return {
            'project': project,
            'current_date': date.today().isoformat(),
            'error_ping': 'All fields are required.'
        }

    try:
        new_task = Task(
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
        return {
            'task': task,
            'project': project,
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

        task.task_title = name
        task.task_description = description
        task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
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
        request.dbsession.delete(task)
        request.dbsession.flush()
        return HTTPFound(location=request.route_url('project_by_id', id=project_id))
    except Exception as e:
        request.dbsession.rollback()
        return HTTPBadRequest(f"Error deleting task: {str(e)}")