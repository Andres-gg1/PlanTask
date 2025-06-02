import pytest
from webtest import TestApp
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
import allure

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
    return project

@allure.feature("Projects")
@allure.story("Project Creation")
@allure.title("Create project and verify fields")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_project_flow(created_project):
    with allure.step("Verify project creation and its fields"):
        assert created_project is not None
        assert created_project.name == 'Proyecto de prueba'
        assert created_project.description == 'Descripción de prueba'


@allure.feature("Projects")
@allure.story("Project Page Access")
@allure.title("Access created project page")
@allure.severity(allure.severity_level.NORMAL)
def test_project_page_access(testapp, created_project):
    project_id = int(created_project.id)
    with allure.step("Access project page and check content"):
        res = testapp.get(f'/project/{project_id}')
        assert res.status_code == 200
        assert 'Proyecto de prueba' in res.text
        assert 'Descripción de prueba' in res.text

@allure.feature("Projects")
@allure.story("Project Page Access")
@allure.title("Access non-existent project page returns 404")
@allure.severity(allure.severity_level.MINOR)
def test_project_page_access_not_found(testapp):
    with allure.step("Try to access a non-existent project and expect 404"):
        res = testapp.get('/project/999999', status=404)
        assert res.status_code == 404


@allure.feature("Projects")
@allure.story("Project Edit")
@allure.title("Access project edit page and verify contents")
@allure.severity(allure.severity_level.NORMAL)
def test_edit_project(testapp, created_project):
    project_id = int(created_project.id)
    with allure.step("Access edit project page and check form fields"):
        res = testapp.get(f'/project/{project_id}/edit')
        assert res.status_code == 200
        assert 'Proyecto de prueba' in res.text
        assert 'Descripción de prueba' in res.text
        assert 'csrf_token' in res.text


@allure.feature("Projects")
@allure.story("Project Edit")
@allure.title("Submit edited project form and verify changes")
@allure.severity(allure.severity_level.CRITICAL)
def test_edit_project_submission(testapp, created_project, dummy_admin_user):
    project_id = created_project.id
    with allure.step("Fetch CSRF token from edit page"):
        res = testapp.get(f'/project/{project_id}/edit')
        csrf_token = res.html.find('input', {'name': 'csrf_token'})['value']

    form_data = {
        'name': 'Nuevo Nombre',
        'description': 'Nueva descripcion del proyecto',
        'project_id': str(project_id),
        'csrf_token': csrf_token    
    }

    with allure.step("Submit edit project form and follow redirect"):
        response = testapp.post(
            f'/project/{project_id}/edit',
            params=form_data,
            status=302
        )
        followup = response.follow()
        assert b'Nuevo Nombre' in followup.body
        assert b'Nueva descripcion' in followup.body

@allure.feature("Labels")
@allure.story("Label Management")
@allure.title("Create label and verify display")
@allure.severity(allure.severity_level.NORMAL)
def test_project_labels_display_and_creation(testapp, created_project, dbsession, dummy_admin_user):
    project_id = created_project.id
    with allure.step("Add a label to the project"):
        res = testapp.get(f'/project/{project_id}')
        csrf_token = res.html.find('input', {'name': 'csrf_token'})['value']
        label_data = {
            'label_name': 'Urgent',
            'label_color': '#ff0000',
            'relation': False,
            'csrf_token': csrf_token
        }
        testapp.post(f'/project/{project_id}/add-label', params=label_data, status=302)
    with allure.step("Check label appears on project page"):
        res = testapp.get(f'/project/{project_id}')
        assert 'Urgent' in res.text
        assert '#ff0000' in res.text


@allure.feature("Members")
@allure.story("Member Management")
@allure.title("Add and promote a member to Project Manager")
@allure.severity(allure.severity_level.CRITICAL)
def test_add_and_promote_member(testapp, created_project, dbsession, dummy_admin_user):
    project_id = created_project.id
    with allure.step("Create a new user to add"):
        new_user = User(
            username='testuser',
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password='password',
            active=True
        )
        dbsession.add(new_user)
        dbsession.flush()
    with allure.step("Add the user as a member"):
        res = testapp.get(f'/project/{project_id}')
        csrf_token = res.html.find('input', {'name': 'csrf_token'})['value']
        add_member_data = {
            'user_ids': [str(new_user.id)],
            'role': 'member',
            'csrf_token': csrf_token
        }
        testapp.post(f'/project/{project_id}/add-member', params=add_member_data, status=302)
    with allure.step("Promote the user to project manager"):
        promote_data = {
            'user_id': str(new_user.id),
            'role': 'project_manager',
            'csrf_token': csrf_token,
            'labels': []
        }
        testapp.post(f'/project/{project_id}/edit-member', params=promote_data, status=302)
    with allure.step("Check the user is now a project manager"):
        res = testapp.get(f'/project/{project_id}')
        assert 'Project Manager' in res.text
        assert 'testuser' in res.text


@allure.feature("Members")
@allure.story("Member Management")
@allure.title("Remove a member from a project")
@allure.severity(allure.severity_level.NORMAL)
def test_remove_member(testapp, created_project, dbsession, dummy_admin_user):
    project_id = created_project.id
    with allure.step("Create and add a user"):
        user = User(
            username='removeuser',
            email='removeuser@example.com',
            first_name='Remove',
            last_name='User',
            password='password',
            active=True
        )
        dbsession.add(user)
        dbsession.flush()
    with allure.step("Add as member"):
        res = testapp.get(f'/project/{project_id}')
        csrf_token = res.html.find('input', {'name': 'csrf_token'})['value']
        add_member_data = {
            'user_ids': [str(user.id)],
            'role': 'member',
            'csrf_token': csrf_token
        }
        testapp.post(f'/project/{project_id}/add-member', params=add_member_data, status=302)
    with allure.step("Remove member"):
        remove_data = {
            'user_id': str(user.id),
            'csrf_token': csrf_token
        }
        testapp.post(f'/project/{project_id}/remove-member', params=remove_data, status=302)
    with allure.step("Check user is not in members list"):
        res = testapp.get(f'/project/{project_id}')
        assert 'removeuser' not in res.text

@allure.feature("Kanban Board")
@allure.story("Task Display by Status")
@allure.title("Verify Kanban board groups tasks by status correctly")
@allure.severity(allure.severity_level.NORMAL)
def test_kanban_board_grouping(testapp, created_project, dbsession, dummy_admin_user):
    project_id = created_project.id
    statuses = ['assigned', 'in_progress', 'under_review', 'completed']
    with allure.step("Create tasks with different statuses"):
        for i, status in enumerate(statuses):
            task = Task(
                project_id=project_id,
                task_title=f'Task {status}',
                task_description=f'Description {status}',
                status=status,
                active=True
            )
            dbsession.add(task)
        dbsession.flush()
    with allure.step("Check that each status column contains the correct task"):
        res = testapp.get(f'/project/{project_id}')
        for status in statuses:
            assert f'Task {status}' in res.text
            assert f'Description {status}' in res.text


@allure.feature("Admin UI")
@allure.story("Admin Controls Visibility")
@allure.title("Verify admin controls are visible on the project page")
@allure.severity(allure.severity_level.MINOR)
def test_admin_actions_visibility(testapp, created_project, dummy_admin_user):
    project_id = created_project.id
    with allure.step("Check that admin actions/buttons are visible"):
        res = testapp.get(f'/project/{project_id}')
        assert 'Edit Project' in res.text
        assert 'Delete Project' in res.text
        assert 'Add Member' in res.text
        assert 'Add Label' in res.text