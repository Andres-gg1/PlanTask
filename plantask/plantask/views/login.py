from ..models import User
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy import or_
import argon2
from pyramid.security import remember
from pyramid.httpexceptions import HTTPFound
from datetime import datetime, timedelta
import json

TRUSTED_IPS = {"123.45.67.89"}
PING_CODE = "KOCH1234"

@view_config(route_name='login', renderer='/templates/login.jinja2', request_method='GET')
def login_page(request):
    return {}

@view_config(route_name='login', renderer='json', request_method='POST')
def login_user(request):
    psw_hasher = argon2.PasswordHasher()
    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('password')
    ip_address = request.remote_addr
    ping_code = request.POST.get('ping_code')

    if ip_address not in TRUSTED_IPS:
        return Response(json_body={"error": "Untrusted IP address"}, status=403)

    if ping_code != PING_CODE:
        return Response(json_body={"error": "Invalid Ping Code"}, status=403)

    user = request.dbsession.query(User).filter(or_(User.username == username, User.email == email)).first()
    if user:
        if psw_hasher.verify(user.password, password):
            headers = remember(request, str(user.id))
            request.session['role'] = user.permission
            request.session['expires_at'] = datetime.now() + timedelta(minutes=30)
            return HTTPFound(location=request.route_url('home'), headers=headers)
        return Response(json_body={"error": "Invalid credentials"}, status=401)
    return Response(json_body={"error": "User not found"}, status=404)

@view_config(route_name='validate_ip', renderer='json', request_method='POST')
def validate_ip(request):
    ip_address = request.remote_addr
    return {"isTrusted": ip_address in TRUSTED_IPS}

@view_config(route_name='validate_code', renderer='json', request_method='POST')
def validate_code(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        return {"isValid": data.get("code") == PING_CODE}
    except json.JSONDecodeError:
        return {"isValid": False}