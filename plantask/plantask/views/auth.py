from ..models import User, ActivityLog
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy import or_
import argon2
from pyramid.security import remember
from pyramid.httpexceptions import HTTPFound
from datetime import datetime, timedelta
from ..auth.network import is_ip_trusted, is_valid_ping_code
from re import search 
from random import randint
from pyramid.security import forget


def validate_password(password):
    errors = []
    if len(password) < 8:
        errors.append("The password must be at least 8 characters long.")
    if not search(r'[a-z]', password):
        errors.append("The password must contain at least one lowercase letter.")
    if not search(r'[A-Z]', password):
        errors.append("The password must contain at least one uppercase letter.")
    if not search(r'\d', password):
        errors.append("The password must contain at least one number.")
    if not search(r'\W', password):
        errors.append("The password must contain at least one non-alphanumeric character.")
    if password and (password[0].isspace() or password[-1].isspace()):
        errors.append("The password cannot begin or end with a blank space.")

    return errors if errors else None


@view_config(route_name='login', renderer='/templates/login.jinja2', request_method='GET')
def login_page(request):
    ip_address = request.remote_addr
    show_modal = not is_ip_trusted(ip_address) and not request.session.get("pingid_ok", False)
    return {"show_modal": show_modal}


@view_config(route_name='login', renderer='/templates/login.jinja2', request_method='POST', require_csrf=True)
def login_user(request):
    try:
        ip_address = request.remote_addr
        ping_code = request.POST.get("pingCode")
        email = request.POST.get("loginEmail")
        password = request.POST.get("loginPassword")
        psw_hasher = argon2.PasswordHasher()

        MAX_ATTEMPTS = 5

        if "current_attempt" not in request.session:
            request.session["current_attempt"] = 0
        if "failed_email_attempts" not in request.session:
            request.session["failed_email_attempts"] = []

        if not is_ip_trusted(ip_address) and not request.session.get("pingid_ok", False):
            if not ping_code:
                return {"show_modal": True, "error_ping": ""}
            if not is_valid_ping_code(ping_code):
                return {"show_modal": True, "error_ping": "Incorrect code."}
            request.session["pingid_ok"] = True
            return HTTPFound(location=request.route_url("login"))

        if not all([email, password]):
            return {"show_modal": False, "error_ping": "Missing required fields."}

        if not email.endswith("@kochcc.com"):
            return {"show_modal": False, "error_ping": "Invalid email domain."}

        if request.session["current_attempt"] >= MAX_ATTEMPTS:
            activity_log = ActivityLog(
                timestamp=datetime.now(),
                action="login_several_failed_attempts",
                changes=f"IP address: {ip_address}, Email/s used: {request.session['failed_email_attempts']}",
            )
            request.dbsession.add(activity_log)
            return {"show_modal": False, "error_ping": "Too many failed attempts. Please try again later."}

        user = request.dbsession.query(User).filter(User.email == email).first()

        if user:
            try:
                if psw_hasher.verify(user.password, password):
                    headers = remember(request, str(user.id))
                    request.session['role'] = user.permission
                    request.session['username'] = user.username
                    request.session['user_id'] = user.id
                    request.session['expires_at'] = str(datetime.now() + timedelta(minutes=30))
                    request.session.pop("pingid_ok", None)
                    request.session.pop("failed_email_attempts", None)
                    request.session.pop("current_attempt", None)

                    return HTTPFound(location=request.route_url('home'), headers=headers)

            except argon2.exceptions.VerifyMismatchError:
                request.session["current_attempt"] += 1
                if email not in request.session["failed_email_attempts"]:
                    request.session["failed_email_attempts"].append(email)

                return {"show_modal": False, "error_ping": "Incorrect password."}

        return {"show_modal": False, "error_ping": "Invalid credentials."}

    except Exception as e:
        return {"show_modal": False, "error_ping": f"Internal server error. {e}" }

@view_config(route_name='logout')
def logout_user(request):
    """
    Logs out the user by clearing their session and redirecting to the login page.
    """
    headers = forget(request)  # Clear authentication headers
    request.session.invalidate()  # Clear the session
    return HTTPFound(location=request.route_url('login'), headers=headers)

@view_config(route_name='register', renderer='/templates/register.jinja2', request_method='GET', permission="admin")
def register_user_page(request):
    ip_address = request.remote_addr
    show_modal = not is_ip_trusted(ip_address) and not request.session.get("pingid_ok", False)
    return {"show_modal": show_modal}



@view_config(route_name='register', renderer='/templates/register.jinja2', request_method='POST', permission="admin", require_csrf=True)
def register_user(request):
    ip_address = request.remote_addr
    ping_code = request.POST.get("pingCode")

    # IP verification for untrusted networks
    if not is_ip_trusted(ip_address) and not request.session.get("pingid_ok", False):
        if not ping_code:
            return {"show_modal": True, "error_ping": ""}
        if not is_valid_ping_code(ping_code):
            return {"show_modal": True, "error_ping": "Incorrect code."}
        request.session["pingid_ok"] = True
        return HTTPFound(location=request.route_url("register"))

    psw_hasher = argon2.PasswordHasher()
    firstname = request.POST.get('signupFirstname')
    lastname = request.POST.get('signupLastname')
    email = request.POST.get('signupEmail')
    password = request.POST.get('password')
    confirm_password = request.POST.get('confirm_password')
    permission = request.POST.get('permission', 'user')  # default to "user" if not specified

    if not email.endswith("@kochcc.com"):
        return {"show_modal": False, "error_ping": "Invalid email domain."}

    # Password validation
    password_errors = validate_password(password)
    if password_errors:
        return {
            "show_modal": False,
            "error_ping": "<br>".join(password_errors),
            "form_data": {
                "signupFirstname": firstname,
                "signupLastname": lastname,
                "signupEmail": email,
                "permission": permission,
            },
        }

    if password != confirm_password:
        return {
            "show_modal": False,
            "error_ping": "Passwords do not match.",
            "form_data": {
                "signupFirstname": firstname,
                "signupLastname": lastname,
                "signupEmail": email,
                "permission": permission,
            },
        }

    username = generate_unique_username(firstname, lastname, request.dbsession)

    user = request.dbsession.query(User).filter(User.email == email).first()
    if user:
        return {
            "show_modal": False,
            "error_ping": "Email already registered.",
            "form_data": {
                "signupFirstname": firstname,
                "signupLastname": lastname,
                "signupEmail": email,
                "permission": permission,
            },
        }

    hashed_password = psw_hasher.hash(password)

    new_user = User(first_name=firstname,last_name = lastname,username=username, email=email, password=hashed_password, permission=permission)
    request.dbsession.add(new_user)
    request.dbsession.flush()
    return HTTPFound(location=request.route_url('home'))

@view_config(route_name='invalid_permissions', renderer='/templates/invalid_permissions.jinja2', request_method='GET')
def invalid_permissions(request):
    return {}

def generate_unique_username(firstname, lastname, dbsession):
    """
    Generate a unique username based on the first three characters of the first and last name,
    followed by a random number between 1 and 1000. If the username already exists, retry with
    a new random number until a unique username is found.
    """
    while True:
        username = f"{firstname[:3]}_{lastname[:3]}{randint(1, 1000)}"
        existing_user = dbsession.query(User).filter(User.username == username).first()
        if not existing_user:
            return username