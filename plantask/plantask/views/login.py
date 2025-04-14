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
    if request.method == 'POST':
        try:

            data = request.POST 

            if not data:
                return Response(json_body={"error": "No data provided"}, status=403)
            
            psw_hasher = argon2.PasswordHasher()

            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            ping_code = data.get('ping_code')

            ip_address = request.remote_addr

            if not all([username, email, password, ping_code]):
                return Response(json_body={"error": "Missing required fields"}, status=403)
            
            if not email.endswith("@kochcc.com"):
                #ADD
                # Log the invalid email attempt if the user has failed multiple times
                # Save -> IP address and email to a database for further analysis
                return Response(json_body={"error": "Invalid email domain"}, status=403)

            if ip_address not in TRUSTED_IPS:
                #ADD
                # Log the untrusted IP address attempt
                # Save -> IP address and (maybe) machine name to a database for further analysis
                return Response(json_body={"error": "Untrusted IP address"}, status=403)

            if ping_code != PING_CODE:
                return Response(json_body={"error": "Invalid Ping Code"}, status=403)

            user = request.dbsession.query(User).filter(or_(User.username == username, User.email == email)).first()
            
            if user:
                try:
                    if psw_hasher.verify(user.password, password):
                        headers = remember(request, str(user.id))
                        request.session['role'] = user.permission
                        request.session['expires_at'] = datetime.now() + timedelta(minutes=30)
                        return HTTPFound(location=request.route_url('home'), headers=headers)
                except argon2.exceptions.VerifyMismatchError:
                    return Response(json_body={"error": "Invalid password"}, status=403)
            return Response(json_body={"error": "Invalid credentials"}, status=401)
        except Exception as e:
            return Response(json_body={"error": "Internal server error"}, status=500)
    return Response(json_body={"error": "Invalid request method"}, status=405)

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