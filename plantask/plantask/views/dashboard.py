from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.auth.verifysession import verify_session

@view_config(route_name='dashboard', renderer='plantask:templates/dashboard.jinja2')
@verify_session
def dashboard_page(request):
    return {}
