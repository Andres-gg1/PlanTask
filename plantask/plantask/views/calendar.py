from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project
from plantask.auth.verifysession import verify_session
from plantask.models.task import Task
from plantask.models.project import ProjectsUser
from plantask.models.label import Label
from plantask.models.label import Label, LabelsTask, LabelsProjectsUser
from plantask.models.project import Project, ProjectsUser
from dateutil.parser import parse as parse_date



@view_config(route_name='calendar', renderer='plantask:templates/calendar.jinja2')
@verify_session
def calendar_page(request):
    # No project_id needed, just render the calendar for the user
    return {}

@view_config(route_name='api_tasks', renderer='json')
@verify_session
def api_tasks(request):
    try:
        project_id = int(request.GET.get('project_id', 0))
    except (ValueError, TypeError):
        raise HTTPNotFound()
    try:
        tasks = request.dbsession.query(Task).filter_by(project_id=project_id, active=True).all()
    except SQLAlchemyError:
        raise HTTPNotFound()
    events = []
    for task in tasks:
        events.append({
            'id': task.id,
            'title': task.task_title,
            'start': task.due_date.strftime('%Y-%m-%d'),
            'status': task.status
        })
    return events

@view_config(route_name='api_user_tasks', renderer='json', request_method='GET')
@verify_session
def api_user_tasks(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return {"error": "No user"}

    # Get user's labels by project
    user_labels_by_project = {}
    labels_user_query = (
        request.dbsession.query(
            LabelsProjectsUser.labels_id,
            Project.id.label("project_id")
        )
        .join(ProjectsUser, ProjectsUser.id == LabelsProjectsUser.projects_users_id)
        .join(Project, Project.id == ProjectsUser.project_id)
        .filter(ProjectsUser.user_id == user_id)
    )
    for label_id, project_id in labels_user_query.all():
        user_labels_by_project.setdefault(project_id, set()).add(label_id)

    # Get user's projects
    projects_query = (
        request.dbsession.query(Project.id)
        .join(ProjectsUser, Project.id == ProjectsUser.project_id)
        .filter(
            ProjectsUser.user_id == user_id,
            ProjectsUser.active.is_(True),
            Project.active.is_(True)
        )
    )

    user_tasks = []
    for project in projects_query.all():
        tasks = (
            request.dbsession.query(Task)
            .filter(Task.project_id == project.id, Task.active.is_(True))
            .all()
        )
        for task in tasks:
            labels = (
                request.dbsession.query(Label.id)
                .join(LabelsTask, Label.id == LabelsTask.labels_id)
                .filter(LabelsTask.tasks_id == task.id)
                .all()
            )
            task_label_ids = {l.id for l in labels}
            user_label_ids = user_labels_by_project.get(project.id, set())
            if user_label_ids & task_label_ids:
                user_tasks.append({
                    "id": task.id,
                    "title": task.task_title,
                    "description": getattr(task, 'description', ''),
                    "start": task.due_date.isoformat() if task.due_date else None,
                    "status": task.status,
                    "project_id": task.project_id,
                })

    return {"tasks": user_tasks}

@view_config(route_name='api_update_task_due_date', request_method='POST', renderer='json')
@verify_session
def api_update_task_due_date(request):
    user_id = request.session.get('user_id')
    data = request.json_body
    if not data or 'id' not in data or 'due_date' not in data:
        return {'status': 'error', 'message': 'Missing id or due_date'}
    try:
        task_id = int(data['id'])
    except (ValueError, TypeError):
        return {'status': 'error', 'message': 'Invalid task id'}

    new_due_date = data['due_date']

    try:
        task = request.dbsession.query(Task).filter_by(id=task_id, active=True).first()
        if not task:
            return {'status': 'error', 'message': 'Task not found'}

        # Check permission
        user_labels = set(
            l.labels_id for l in request.dbsession.query(LabelsProjectsUser)
            .join(ProjectsUser, ProjectsUser.id == LabelsProjectsUser.projects_users_id)
            .filter(ProjectsUser.user_id == user_id, ProjectsUser.project_id == task.project_id)
        )
        task_labels = set(
            l.labels_id for l in request.dbsession.query(LabelsTask)
            .filter(LabelsTask.tasks_id == task.id)
        )
        if not (user_labels & task_labels):
            return {'status': 'error', 'message': 'You do not have permission to update this task'}
        try:
            parsed_due_date = parse_date(new_due_date)
        except ValueError:
            return {'status': 'error', 'message': 'Invalid date format'}

        task.due_date = parsed_due_date
        request.dbsession.flush()
        return {'status': 'ok'}

    except SQLAlchemyError:
        request.dbsession.rollback()
        return {'status': 'error', 'message': 'Database error'}

