from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project
from plantask.auth.verifysession import verify_session
from plantask.models.task import Task

@view_config(route_name='create_task', renderer='plantask:templates/create_task.jinja2', request_method='GET', permission="admin")
@verify_session
def create_task_page(request):
    project_id = request.matchdict.get('project_id')
    project = request.dbsession.query(Project).get(project_id)
    if not project:
        return HTTPFound(location=request.route_url('my_projects')) 
    
    return {'project': project}


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
            'error_ping': 'An error occurred while creating the task. Please try again.'
        }