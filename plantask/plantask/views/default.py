from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project
from plantask.auth.verifysession import verify_session


@view_config(route_name='home', renderer='plantask:templates/home.jinja2')
@verify_session
def my_view(request):
    return {}
