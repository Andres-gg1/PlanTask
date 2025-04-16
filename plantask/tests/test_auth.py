from sqlalchemy import inspect
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from sqlalchemy.exc import OperationalError, SQLAlchemyError

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plantask.models.user import User
from plantask.models.base import Base

import pytest 
import allure

TESTING_DATABASE_URL = "postgresql://postgres:DRbfLrlvWYCYCULVimbRZxufXbujGHaK@trolley.proxy.rlwy.net:35649/railway"

# This URL is for a PostgreSQL database hosted on Railway. Use this to run the application in production.
DATABASE_URL = "postgresql://postgres:hqDGUoMpypystmdWLOYHdzOMrABijDKi@hopper.proxy.rlwy.net:32534/railway"

DATABASES_URL = [
    DATABASE_URL,
    TESTING_DATABASE_URL
]


def engine_test_database():
    try:
        engine = create_engine(TESTING_DATABASE_URL)
        Session = scoped_session(sessionmaker(bind=engine))
        session = Session()
        admin = session.query(User).filter(
            User.id == "1", 
            User.permission =="Admin"            
        ).first()  
        return engine, session, admin
    except OperationalError as e:
        print("Error connecting to the database:", e)

    except SQLAlchemyError as e:
        print("SQLAlchemy error occurred:", e)
    except Exception as e:
        print("An unexpected error occurred:", e)

# The admin should be able to manipulate the users crud freely
# The normal user should be able to just get they user (to login)
#
# pytest fixture to create a session and engine once
        
@pytest.fixture(scope='module')
def setup_database():
    engine, session, admin = engine_test_database()
    yield session  # Provide the session for tests
    session.close()  # Clean up after the test is done

class TestNonAdminPrivileges:
    def test_normalLogin():
        pass
    def test_untrustedIpAccess():
        pass
    def test_viewsSecurity(): #This will be uptaded any time a new view is added
        pass
    def test_severalFailedLoginAttempts():
        pass
    def test_badPassword():
        pass
    def test_trustedEmailExtensions():
        pass
    def test_missingFields():
        pass

from sqlalchemy.exc import IntegrityError

def create_user(session, username, first_name, last_name, email, password, permission):
    """Helper function to create a user"""
    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        permission=permission
    )
    session.add(user)
    session.flush()
    return user


class TestAdminPrivileges:

    @pytest.mark.parametrize(
        "username, first_name, last_name, email, password, permission",
        [
            ("admin_user", "Admin", "User", "admin@example.com", "adminpassword", "Admin"),
            ("nonpriv_user", "Non", "Priv", "nonpriv@example.com", "userpassword", "User")
        ]
    )
    def test_insert_user(self, setup_database, username, first_name, last_name, email, password, permission):
        # Get the session from the fixture
        session = setup_database
        
        # Create a new user
        new_user = create_user(session, username, first_name, last_name, email, password, permission)

        # Fetch the user to verify it was inserted correctly
        inserted_user = session.query(User).filter_by(username=username).first()

        assert inserted_user is not None, f"User {username} was not inserted correctly."
        assert inserted_user.username == username, f"Expected {username}, but got {inserted_user.username}"
        assert inserted_user.permission == permission, f"Expected {permission} permission, but got {inserted_user.permission}"

    def test_insert_user_with_missing_fields(self, setup_database):
        """Test user creation with missing fields, such as password or email"""
        session = setup_database
        
        # Create a user with missing fields (e.g., missing password)
        missing_fields_user = User(
            username="missing_user",
            first_name="Missing",
            last_name="Fields",
            email=None,  # Missing email
            password=None,  # Missing password
            permission="User"
        )
        
        # Try to add the user to the session
        try:
            session.add(missing_fields_user)
            session.commit()
            assert False, "Expected IntegrityError due to missing fields, but no error occurred."
        except IntegrityError as e:
            session.rollback()  # Rollback the session after the error
            assert "null value in column" in str(e), f"Unexpected error: {str(e)}"

    def test_insert_user_with_existing_email(self, setup_database):
        """Test user creation with an already existing email"""
        session = setup_database
        
        # First, create a user
        create_user(session, "unique_user", "First", "Last", "unique@example.com", "password", "Admin")
        
        # Try to create another user with the same email
        duplicate_user = User(
            username="duplicate_user",
            first_name="Dup",
            last_name="User",
            email="unique@example.com",  # Same email as the first user
            password="password",
            permission="User"
        )
        
        try:
            session.add(duplicate_user)
            session.commit()
            assert False, "Expected IntegrityError due to duplicate email, but no error occurred."
        except IntegrityError as e:
            session.rollback()  # Rollback the session after the error
            assert "duplicate key value violates unique constraint" in str(e), f"Unexpected error: {str(e)}"


    def test_updateUser():
        pass
    def test_getUser():
        pass
    def test_deleteUser():
        pass
    def test_promoteUser():
        pass
    def test_demoteUser():
        pass