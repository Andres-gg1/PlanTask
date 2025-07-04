import pytest
from webtest import TestApp
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Ensure that the project root directory is in the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from plantask.models.user import User
from plantask.models.base import Base
from plantask import main

# URL for the testing database
TESTING_DATABASE_URL = "postgresql://postgres:DRbfLrlvWYCYCULVimbRZxufXbujGHaK@trolley.proxy.rlwy.net:35649/railway"

@pytest.fixture
def testapp():
    # Setup the app for testing with specific settings
    settings = {
        'sqlalchemy.url': TESTING_DATABASE_URL,
        'testing': True,
        'smtp.host': 'localhost',
        'smtp.port': '1025',
        'smtp.username': 'dummy',
        'smtp.password': 'dummy',
        'smtp.from': 'test@example.com',
    }
    app = main({}, **settings)
    test_app = TestApp(app)

    # Cleanup after the test has finished
    yield test_app
    dbsession = app.registry['dbsession_factory']()
    dbsession.commit()
    dbsession.close()

# Tests for invalid passwords during registration
@pytest.mark.parametrize("password", [
    "short1!",                   # less than 8 characters
    "alllowercase1!",            # no uppercase letters
    "ALLUPPERCASE1!",            # no lowercase letters
    "NoNumber!",                 # no numbers
    "NoSpecial1",                # no special characters
    " Leading1!",                # leading space
    "Trailing1! ",               # trailing space
    "     ",                     # only spaces
    "ValidButNoMatch1!",         # valid but doesn't match the confirmation
    "NoDigitsOrSpecials"         # no digits or special characters
])
def test_register_invalid_passwords(testapp, password):
    # Fetch CSRF token from registration page
    res_get = testapp.get('/register', expect_errors=True)
    try:
        csrf_token = res_get.html.find('input', {'name': 'csrf_token'})
        token_value = csrf_token['value'] if csrf_token else ''
    except AttributeError:
        token_value = ''
    # Prepare registration data with the invalid password
    data = {
        'signupFirstname': 'Test',
        'signupLastname': 'User',
        'signupEmail': 'testuser@kochcc.com',
        'password': password,
        'confirm_password': 'Different123!' if password == "ValidButNoMatch1!" else password,
        'permission': 'user',
        'csrf_token': token_value
    }
    # Simulate an untrusted IP to trigger the network verification modal
    res = testapp.post('/register', params=data, extra_environ={'REMOTE_ADDR': '8.8.8.8'}, expect_errors=True)
    if res.status_int == 302:
        res = res.follow()
    assert res.status_int == 200
    print(res.text)
    # Check if the network verification modal is shown
    assert "Network Verification Required" in res.text


def test_normal_login_with_untrusted_ip(testapp):
    # Fetch CSRF token from login page
    res_get = testapp.get('/login', expect_errors=True)
    try:
        csrf_token = res_get.html.find('input', {'name': 'csrf_token'})
        token_value = csrf_token['value'] if csrf_token else ''
    except AttributeError:
        token_value = ''
    # Simulate a normal login attempt from an untrusted IP
    data = {
        'loginEmail': 'testuser@kochcc.com',
        'loginPassword': "SecurePassword1!",
        'csrf_token': token_value
    }
    res = testapp.post('/login', params=data, extra_environ={'REMOTE_ADDR': '1.1.1.1'})
    assert res.status_int == 200
    # Check if the network verification modal is shown
    assert "Network Verification Required" in res.text


def test_normal_login_with_trusted_ip(testapp):
    # Fetch CSRF token from login page
    res_get = testapp.get('/login', expect_errors=True)
    try:
        csrf_token = res_get.html.find('input', {'name': 'csrf_token'})
        token_value = csrf_token['value'] if csrf_token else ''
    except AttributeError:
        token_value = ''
    # Simulate a normal login attempt from a trusted IP
    data = {
        'loginEmail': 'testuser@kochcc.com',
        'loginPassword': "SecurePassword1!",
        'csrf_token': token_value
    }
    res = testapp.post('/login', params=data, extra_environ={'REMOTE_ADDR': '123.45.67.89'})
    assert res.status_int == 200
    # Check if the network verification modal is NOT shown
    assert "Network Verification Required" not in res.text
