from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project
from plantask.models.file import File
from plantask.models.activity_log import ActivityLog
from plantask.auth.verifysession import verify_session


def serialize_activity_log(log, request):
    """Convert ActivityLog object to a dictionary."""
    project_image = None
    if log.project and log.project.project_image_id:
        image_route = request.dbsession.query(File).filter_by(id=log.project.project_image_id).first()
        if image_route:
            project_image = image_route.route


    return {
        "id": log.id,
        "user_id": log.user_id,
        "username": log.user.username,  # Add username
        "first_name": log.user.first_name,  # Add first name
        "last_name": log.user.last_name,  # Add last name
        "email": log.user.email,  # Add email
        "object_user_id": log.object_user_id,
        "object_user_first_name": log.object_user.first_name if log.object_user else None,
        "object_user_last_name": log.object_user.last_name if log.object_user else None,
        "project_id": log.project_id if log.project else None,
        "project_is_active" : bool(log.project.active) if log.project else None,
        "project_name": log.project.name if log.project else None,
        "project_image": project_image,
        "task_id": log.task_id,
        "microtask_id": log.microtask_id,
        "file_id": log.file_id,
        "groupchat_id": log.groupchat_id,
        "timestamp": log.timestamp.isoformat(',' , "milliseconds"),
        "action": log.action,
        "changes": log.changes,
    }


@view_config(route_name='history', renderer='plantask:templates/history.jinja2')
@verify_session
def history_page(request):
    user_id = request.session['user_id']
    role = request.session['role']

    if role == 'admin':
        actions = request.dbsession.query(ActivityLog).all()
        actions = [serialize_activity_log(action, request) for action in actions]  # Serialize objects
    else:
        actions = []

    my_actions = request.dbsession.query(ActivityLog).filter_by(user_id=user_id).all()
    my_actions = [serialize_activity_log(action, request) for action in my_actions]  # Serialize objects

    return {
        "actions": actions,
        "my_actions": my_actions,
    }


