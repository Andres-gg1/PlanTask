from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Allow
from pyramid.httpexceptions import HTTPFound
from pyramid.view import forbidden_view_config
from pyramid.session import SignedCookieSessionFactory
from pyramid.events import subscriber, BeforeRender
from .models.user import User
from .models.file import File
from pyramid.csrf import get_csrf_token
from pyramid.csrf import CookieCSRFStoragePolicy

class RootFactory:
    # Creates user privileges to separate admins from end users
    __acl__ = [
        (Allow, 'role:admin', 'admin'),
        (Allow, 'role:user', 'user'),
        (Allow, 'role:pm', 'pm'),
    ]
    def __init__(self, request):
        pass

@forbidden_view_config()
def forbidden_view(request):
    if not request.authenticated_userid:
        # User not auth -> redirect to login
        return HTTPFound(location=request.route_url('login'))
    else:
        # User is auth but does not have permission -> permissions invalid 
        return HTTPFound(location=request.route_url('invalid_permissions'))

@subscriber(BeforeRender)
def add_global_template_variables(event):
    request = event['request']
    if request.authenticated_userid:
        user = request.dbsession.query(
                User.id,
                User.username,
                User.first_name,
                User.last_name,
                User.email,
                File.route.label('image_route')  # Fetch the route from the File model
            ).outerjoin(
                File, User.user_image_id == File.id  # Use an outer join to handle users without images
            ).filter(
                User.id == request.authenticated_userid
            ).first()
        if user:
            event['user'] = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'pfp' : user.image_route
            }
    else:
        event['user'] = None
    event['active_page'] = request.matched_route.name if request.matched_route else None
    event['role'] = request.session.get('role', None)
    event['csrf_token'] = get_csrf_token(request)

def main(global_config, **settings):
    # This function returns a Pyramid WSGI application.

    secretkey = "sosecretwow"

    # Groupfinder to find user role, either admin or user

    def groupfinder(userid, request):
        user = request.dbsession.query(User).get(userid)
        if user:
            return [f'role:{user.permission}']
        return []   

    # Authentication and Authorization policies
    
    authn_policy = AuthTktAuthenticationPolicy(
        secretkey, 
        hashalg='sha512', 
        cookie_name='auth_tkt', 
        callback=groupfinder,
        secure=True,
        http_only=True,
        samesite='Strict'
    )
    authz_policy = ACLAuthorizationPolicy()

    with Configurator(settings=settings, root_factory=RootFactory) as config:
        config.set_authentication_policy(authn_policy)
        config.set_authorization_policy(authz_policy)

        my_session_factory = SignedCookieSessionFactory(
            secretkey,
            secure=True,
            httponly=True,
            samesite='Strict'
        )
        config.set_session_factory(my_session_factory)
        config.set_csrf_storage_policy(CookieCSRFStoragePolicy())
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.include('.models')
        config.add_static_view(name='static', path='static')

        import plantask.utils.events
        config.scan('plantask.utils.events')

        config.scan()

        # Email sender
    from plantask.utils.smtp_email_sender import SMTPEmailSender
    
    smtp_settings = config.get_settings()
    email_sender = SMTPEmailSender(
        host=smtp_settings['smtp.host'],
        port=int(smtp_settings['smtp.port']),
        username=smtp_settings['smtp.username'],
        password=smtp_settings['smtp.password'],
        from_email=smtp_settings.get('smtp.from')
    )
    config.registry.settings['email_sender'] = email_sender
    return config.make_wsgi_app()