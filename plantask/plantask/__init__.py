from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Allow
from .models.user import User
from pyramid.httpexceptions import HTTPForbidden
from pyramid.view import forbidden_view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.session import SignedCookieSessionFactory  # <-- NUEVO

class RootFactory:
    """
    Creates user privileges to separate admins from end users
    """
    __acl__ = [
        (Allow, 'role:admin', 'admin'),
        (Allow, 'role:user', 'user')
    ]

@forbidden_view_config()
def forbidden_view(request):
    if not request.authenticated_userid:
        # User not auth -> redirect to login
        return HTTPFound(location=request.route_url('login'))
    else:
        # User is auth but does not have permission -> permissions invalid 
        return HTTPFound(location=request.route_url('invalid_permissions'))

from pyramid.events import subscriber, BeforeRender

@subscriber(BeforeRender)
def add_global_template_variables(event):
    request = event['request']
    event['active_page'] = request.matched_route.name if request.matched_route else None
    event['role'] = request.session.get('role', None)

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    secretkey = "sosecretwow"

    """
    Groupfinder to find user role, either admin or user
    """
    def groupfinder(userid, request):
        user = request.dbsession.query(User).get(userid)
        if user:
            return [f'role:{user.permission}']  # role:admin, role:pm, etc.
        return []

    """
    Authentication and Authorization policies
    """
    authn_policy = AuthTktAuthenticationPolicy(secretkey, hashalg='sha512', cookie_name='auth_tkt', callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()

    with Configurator(settings=settings) as config:
        config.set_authentication_policy(authn_policy)
        config.set_authorization_policy(authz_policy)

        my_session_factory = SignedCookieSessionFactory(secretkey)
        config.set_session_factory(my_session_factory)

        config.include('pyramid_jinja2')
        config.include('.routes')
        config.include('.models')
        config.add_static_view(name='static', path='static')

        config.scan()
    return config.make_wsgi_app()
