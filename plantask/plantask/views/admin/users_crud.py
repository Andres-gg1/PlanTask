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

@view_config(route_name='register_user', renderer='/templates/register_user.jinja2', request_method='GET')
def register_user_page(request):
    return {}   

@view_config(route_name='register_user', renderer='json', request_method='POST', permission="admin")
def register_user(request):
    psw_hasher = argon2.PasswordHasher()
    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('password')
    permission = request.POST.get('permission')
    
    user = request.dbsession.query(User).filter(or_(User.username == username, User.email == username)).first()
    
    if user:
        return Response(json_body={"error": "User already exists"})
    
    hashed_password = psw_hasher.hash(password)
    
    new_user = User(username=username, email=email, password=hashed_password, permission=permission)
    request.dbsession.add(new_user)
    
    headers = remember(request, str(new_user.id))
    request.session['role'] = new_user.permission
    request.session['expires_at'] = datetime.now() + timedelta(minutes=30)
    
    return HTTPFound(location=request.route_url('home'), headers=headers)