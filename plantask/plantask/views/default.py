from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden
from sqlalchemy.exc import SQLAlchemyError
from plantask.models.user import User
from plantask.models.file import File
from plantask.models.project import Project
from plantask.auth.verifysession import verify_session


@view_config(route_name='home', renderer='plantask:templates/home.jinja2')
@verify_session
def my_view(request):
    return {}

@view_config(route_name='user', renderer='plantask:templates/user_view.jinja2')
@verify_session
def user_view(request):
    user_id = int(request.matchdict.get('id'))

    # Only load specific fields
    user_viewing = request.dbsession.query(
        User.id,
        User.username,
        User.first_name,
        User.last_name,
        User.email,
        User.permission,
        User.user_image_id
    ).filter_by(id=user_id).first()

    user_image = request.dbsession.query(
        File.route
    ).filter_by(id = user_viewing.user_image_id).scalar()

    if not user_viewing:
        return {"error_ping": "User not found."}

    return { "user_viewing": user_viewing,
            "user_image" : user_image }

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

@view_config(route_name='edit_user', request_method='POST')
@verify_session
def edit_user(request):
    user_id = int(request.matchdict['id'])
    user = request.dbsession.query(User).filter_by(id=user_id).first()

    if not user:
        return HTTPNotFound("User not found.")

    if request.session.get('role') != 'admin' and request.session.get('user_id') != user_id:
        return HTTPForbidden()

    user.first_name = request.params.get('first_name', user.first_name)
    user.last_name = request.params.get('last_name', user.last_name)
    user.email = request.params.get('email', user.email)

    request.dbsession.flush()
    return HTTPFound(location=request.route_url('user', id=user_id))

@view_config(route_name='project_info', request_method=['GET'], renderer = "/templates/project_info.jinja2")
@verify_session
def show_project_info(request):
    return {}
