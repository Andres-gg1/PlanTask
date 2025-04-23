from pyramid.httpexceptions import HTTPFound

def verify_session(func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('role'):
            return HTTPFound(location=request.route_url("login"))
        return func(request, *args, **kwargs)
    return wrapper