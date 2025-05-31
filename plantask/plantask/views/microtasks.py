from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest, HTTPNotFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project
from plantask.auth.verifysession import verify_session
from plantask.models.task import Task
from plantask.models.microtask import Microtask
from datetime import date

@view_config(route_name='create_microtask', renderer='plantask:templates/create_microtask.jinja2', request_method='GET', permission="admin")
@verify_session
def create_microtask_page(request):
    task_id = request.matchdict.get('task_id')
    task = request.dbsession.query(Task).get(task_id)
    if not task:
        return HTTPFound(location=request.route_url('task_by_id', id=task_id))
    
    return {
        'task': task,
        'current_date': date.today().isoformat(),
        'task_due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else ''
    }


@view_config(route_name='create_microtask', renderer='plantask:templates/create_microtask.jinja2', request_method='POST', permission="admin")
@verify_session
def create_microtask(request):
    task_id = request.matchdict.get('task_id')
    task = request.dbsession.query(Task).get(task_id)
    if not task:
        return HTTPFound(location=request.route_url('task_by_id', id=task_id))
    
    microtask_name = request.params.get('name')
    microtask_description = request.params.get('description')
    due_date = request.params.get('due_date')

    # Prepare for validation
    today_str = date.today().isoformat()
    task_due_date_str = task.due_date.strftime('%Y-%m-%d') if task.due_date else ''
    
    if not microtask_name or not microtask_description or not due_date:
        return {
            'task': task,
            'current_date': today_str,
            'task_due_date': task_due_date_str,
            'error_ping': 'All fields are required.'
        }

    # Validate due date is within allowed range
    if due_date < today_str or due_date > task_due_date_str:
        return {
            'task': task,
            'current_date': today_str,
            'task_due_date': task_due_date_str,
            'error_ping': f"Due date must be between {today_str} and {task_due_date_str}."
        }

    try:
        new_microtask = Microtask(
            task_id=task_id,
            name=microtask_name,
            description=microtask_description,
            percentage_complete=0.0,
            date_created=datetime.now(),
            due_date=datetime.strptime(due_date, '%Y-%m-%d'),
            status='undone'
        )

        request.dbsession.add(new_microtask)
        request.dbsession.flush()

        return HTTPFound(location=request.route_url('task_by_id', id=task_id))

    except SQLAlchemyError as e:
        request.dbsession.rollback()
        return {
            'task': task,
            'current_date': today_str,
            'task_due_date': task_due_date_str,
            'error_ping': 'An error occurred while creating the task. Please try again.'
        }
