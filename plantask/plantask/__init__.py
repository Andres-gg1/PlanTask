from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Allow
from models.user import User

class RootFactory:
    """
    Creates user privileges to separate admins from end users
    """
    __acl__ = [
        (Allow, 'role:admin', 'admin'),
        (Allow, 'role:user', 'user')
    ]

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    secretkey = "sosecretwow"

    """
    Authentication and Authorization policies
    """
    authn_policy = AuthTktAuthenticationPolicy(secretkey, hashalg='sha512', cookie_name='auth_tkt', callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()

    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    """
    Groupfinder to find user role, either admin or user
    """
    def groupfinder(userid, request):
        user = request.dbsession.query(User).get(userid)
        if user:
            return [f'role:{user.permission}']  # role:admin, role:pm, etc.
        return []



    with Configurator(settings=settings) as config:
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.include('.models')
        config.scan()
    return config.make_wsgi_app()
