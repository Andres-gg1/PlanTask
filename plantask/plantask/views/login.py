from models import User
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy.orm import or_
import argon2
from pyramid.security import remember

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from datetime import datetime, timedelta


@view_config(route_name='login', renderer='/templates/login.jinja2', request_method='GET')
def login_page(request):
    return {}

@view_config(route_name='login', renderer='json', request_method='POST', permission="admin")
def login_user(request):
    psw_hasher = argon2.PasswordHasher()
    username = request.POST.get('username')
    email = email.POST.get('email')
    password = request.POST.get('password')
    user = request.dbsession.query(User).filter(or_(User.username == username, User.email == username)).first()
    if user:
        if psw_hasher.verify(user.password, password):
            headers = remember(request, str(user.id))
            request.session['role'] = user.permission
            request.session['expires_at'] = datetime.now + timedelta(minutes=30)
            return HTTPFound(location=request.route_url('////'), headers=headers)
        return Response(json_body={})