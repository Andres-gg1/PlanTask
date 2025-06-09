from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPBadRequest, Response
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from sqlalchemy import and_, select
from plantask.models.project import Project, ProjectsUser
from plantask.models.user import User
from plantask.models.activity_log import ActivityLog
from plantask.models.task import Task
from plantask.models.label import Label, LabelsProjectsUser, LabelsTask
from plantask.auth.verifysession import verify_session

from plantask.utils.events import UserAddedToProjectEvent, TaskReadyForReviewEvent

import json

@view_config(route_name='tasks_charts', renderer='/templates/testing_charts.jinja2', request_method='GET')
def testing_charts(request):
    pass

@view_config(route_name='tasks_completed', renderer='json', request_method='GET')
def tasks_completed(request):
    project_id = request.matchdict.get('project_id')
    project = request.dbsession.query(Project).get(project_id)


    if not project:
        raise HTTPNotFound("Project not found")
    
    try:

        tasks = request.dbsession.query(Task).filter(
            Task.project_id == project_id,
            Task.status == 'under_review',
            #Task.percentage_complete == 100
        ).all()

        if not tasks:
            return "A"

        task_data = []
        for task in tasks:
            task_data.append({
                'task_id': task.id,
                'task_name': task.task_title,
                #'completed_at': task.completed_at.strftime('%Y-%m-%d %H:%M:%S') if task.completed_at else None
            })

        return tuple(task_data)
    except SQLAlchemyError as e:
        request.logger.error(f"Database error: {str(e)}")
        return "B"

    return None
