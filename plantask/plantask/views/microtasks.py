from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest, HTTPNotFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project
from plantask.auth.verifysession import verify_session
from plantask.models.task import Task
from plantask.models.microtask import Microtask
from plantask.models.activity_log import ActivityLog
from datetime import date

@view_config(route_name='create_microtask', renderer='plantask:templates/create_item.jinja2', request_method='GET', permission="admin")
@verify_session
def create_microtask_page(request):
    task_id = request.matchdict.get('task_id')
    task = request.dbsession.query(Task).get(task_id)
    if not task:
        return HTTPFound(location=request.route_url('task_by_id', id=task_id))
    
    form_config = {
        'title': 'Create New Microtask',
        'subtitle': f'For task: {task.task_title}',
        'icon': 'bi bi-list-check',
        'gradient': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'accent_color': '#4facfe',
        'name_label': 'Microtask Name',
        'name_placeholder': 'Enter a specific microtask name...',
        'description_placeholder': 'Describe this specific step or subtask...',
        'button_text': 'Create Microtask',
        'action': request.route_url('create_microtask', task_id=task.id),
        'show_date': True,
        'max_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else ''
    }
    
    return {
        'task': task,
        'current_date': date.today().isoformat(),
        'task_due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
        'form_config': form_config
    }


@view_config(route_name='create_microtask', renderer='plantask:templates/create_item.jinja2', request_method='POST', permission="admin")
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
    
    form_config = {
        'title': 'Create New Microtask',
        'subtitle': f'For task: {task.task_title}',
        'icon': 'bi bi-check2-square',
        'gradient': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'accent_color': '#4facfe',
        'name_label': 'Microtask Name',
        'name_placeholder': 'Enter a specific microtask name...',
        'description_placeholder': 'Describe this specific step or subtask...',
        'button_text': 'Create Microtask',
        'action': request.route_url('create_microtask', task_id=task.id),
        'show_date': True,
        'max_date': task_due_date_str
    }
    
    if not microtask_name or not microtask_description or not due_date:
        return {
            'task': task,
            'current_date': today_str,
            'task_due_date': task_due_date_str,
            'form_config': form_config,
            'error_ping': 'All fields are required.'
        }

    # Validate due date is within allowed range
    if due_date < today_str or due_date > task_due_date_str:
        return {
            'task': task,
            'current_date': today_str,
            'task_due_date': task_due_date_str,
            'form_config': form_config,
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

        activity_log_microtask_created = ActivityLog(
                        user_id = request.session['user_id'],
                        project_id = new_microtask.task.project_id,
                        task_id = new_microtask.task_id,
                        microtask_id = new_microtask.id,
                        timestamp = datetime.now(),
                        action = 'microtask_created',
                        changes = f"{new_microtask.name}"
        )
        request.dbsession.add(activity_log_microtask_created)

        request.dbsession.flush()

        return HTTPFound(location=request.route_url('task_by_id', id=task_id))

    except SQLAlchemyError as e:
        request.dbsession.rollback()
        return {
            'task': task,
            'current_date': today_str,
            'task_due_date': task_due_date_str,
            'form_config': form_config,
            'error_ping': 'An error occurred while creating the microtask. Please try again.'
        }
