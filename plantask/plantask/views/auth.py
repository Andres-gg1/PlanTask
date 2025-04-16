from ..models import User
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy import or_
import argon2
from pyramid.security import remember
from pyramid.httpexceptions import HTTPFound
from datetime import datetime, timedelta
from ..auth.network import is_ip_trusted, is_valid_ping_code

@view_config(route_name='login', renderer='/templates/login.jinja2', request_method='GET')
def login_page(request):
    ip_address = request.remote_addr
    show_modal = not is_ip_trusted(ip_address) and not request.session.get("pingid_ok", False)
    return {"show_modal": show_modal}


@view_config(route_name='login', renderer='/templates/login.jinja2', request_method='POST')
def login_user(request):
    try:
        ip_address = request.remote_addr
        ping_code = request.POST.get("pingCode")
        email = request.POST.get("loginEmail")
        password = request.POST.get("loginPassword")
        psw_hasher = argon2.PasswordHasher()

        if not is_ip_trusted(ip_address) and not request.session.get("pingid_ok", False):
            if not ping_code:
                return {"show_modal": True, "error_ping": ""}
            if not is_valid_ping_code(ping_code):
                return {"show_modal": True, "error_ping": "Código incorrecto."}
            request.session["pingid_ok"] = True
            return HTTPFound(location=request.route_url("login"))

        if not all([email, password]):
            return {"show_modal": False, "error_ping": "Faltan datos"}

        if not email.endswith("@kochcc.com"):
            return {"show_modal": False, "error_ping": "Dominio de email inválido"}

        user = request.dbsession.query(User).filter(User.email == email).first()

        if user:
            try:
                if psw_hasher.verify(user.password, password):
                    headers = remember(request, str(user.id))
                    request.session['role'] = user.permission
                    request.session['expires_at'] = datetime.now() + timedelta(minutes=30)
                    request.session.pop("pingid_ok", None)
                    return HTTPFound(location=request.route_url('home'), headers=headers)
            except argon2.exceptions.VerifyMismatchError:
                return {"show_modal": False, "error_ping": "Contraseña incorrecta"}

        return {"show_modal": False, "error_ping": "Credenciales inválidas"}

    except Exception:
        return {"show_modal": False, "error_ping": "Error interno del servidor"}


@view_config(route_name='register', renderer='/templates/register.jinja2', request_method='GET', permission="admin")
def register_user_page(request):
    ip_address = request.remote_addr
    show_modal = not is_ip_trusted(ip_address) and not request.session.get("pingid_ok", False)
    return {"show_modal": show_modal}


@view_config(route_name='register', renderer='/templates/register.jinja2', request_method='POST', permission="admin")
def register_user(request):
    ip_address = request.remote_addr
    ping_code = request.POST.get("pingCode")

    if not is_ip_trusted(ip_address) and not request.session.get("pingid_ok", False):
        if not ping_code:
            return {"show_modal": True, "error_ping": ""}
        if not is_valid_ping_code(ping_code):
            return {"show_modal": True, "error_ping": "Código incorrecto."}
        request.session["pingid_ok"] = True
        return HTTPFound(location=request.route_url("register"))

    psw_hasher = argon2.PasswordHasher()
    username = request.POST.get('signupUsername')
    email = request.POST.get('signupEmail')
    password = request.POST.get('password')
    confirm_password = request.POST.get('confirm_password')
    permission = request.POST.get('permission', 'user')  # default a user si no se indica

    if password != confirm_password:
        return {"show_modal": False, "error_ping": "Las contraseñas no coinciden."}

    user = request.dbsession.query(User).filter(
        or_(User.username == username, User.email == email)
    ).first()

    if user:
        return {"show_modal": False, "error_ping": "El usuario ya existe."}

    hashed_password = psw_hasher.hash(password)

    new_user = User(username=username, email=email, password=hashed_password, permission=permission)
    request.dbsession.add(new_user)

    headers = remember(request, str(new_user.id))
    request.session['role'] = new_user.permission
    request.session['expires_at'] = datetime.now() + timedelta(minutes=30)
    request.session.pop("pingid_ok", None)

    return HTTPFound(location=request.route_url('home'), headers=headers)
