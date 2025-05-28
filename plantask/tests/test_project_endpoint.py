import pytest
from webtest import TestApp
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Ensure that the project root directory is in the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from plantask.models.project import Project, ProjectsUser
from plantask.models.user import User
from plantask.models.activity_log import ActivityLog
from plantask.models.task import Task
from plantask.models.label import Label, LabelsProjectsUser

from plantask.utils.events import UserAddedToProjectEvent, TaskReadyForReviewEvent

from plantask import main
import re

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

import pytest

@pytest.fixture
def dbsession(testapp):
    # Obtén la sesión de la app creada por testapp
    dbsession = testapp.app.registry['dbsession_factory']()
    yield dbsession
    dbsession.rollback()
    dbsession.close()

from bs4 import BeautifulSoup

def get_valid_csrf_token(testapp, path):
    response = testapp.get(path)
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        return csrf_input['value']
    raise ValueError("No CSRF token found in the form")


@pytest.fixture
def validate_session_and_token(testapp):
    data = {
        'loginEmail': 'admin@kochcc.com',
        'loginPassword': '314PLANTASK_SECURE_SUPER_PASSWORD159',
        'csrf_token': get_valid_csrf_token(testapp, '/login')
    }
    res_login = testapp.post('/login', params=data, extra_environ={'REMOTE_ADDR': '123.45.67.89'})
    return res_login

def get_valid_csrf_token(testapp, path='/login'):
    res = testapp.get(path)
    return res.html.find('input', {'name': 'csrf_token'})['value']


@pytest.fixture
def created_project(testapp, dbsession, validate_session_and_token):
    res = testapp.get('/create-project')
    csrf_token = res.html.find('input', {'name': 'csrf_token'})['value']

    testapp.post('/create-project', {
        'name': 'Proyecto de prueba',
        'description': 'Descripción de prueba',
        'csrf_token': csrf_token
    })

    project = dbsession.query(Project).filter_by(name='Proyecto de prueba').first()
    print(f"FUNCT:{project.id}")
    return project
def test_create_project_flow(created_project):
    assert created_project is not None
    assert created_project.description == 'Descripción de prueba'

def test_project_page_access(testapp, created_project):
    project_id = int(created_project.id)
    print(project_id)
    res = testapp.get(f'/project/{project_id}')
    print(res.text)
    assert res.status_code == 200
    assert 'Proyecto de prueba' in res.text

def test_edit_project(testapp, created_project):
    project_id = int(created_project.id)
    print(project_id)
    res = testapp.get(f'/project/{project_id}/edit')
    print(res.text)
    assert res.status_code == 200