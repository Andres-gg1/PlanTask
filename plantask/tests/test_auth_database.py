import pytest
import allure
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from argon2 import PasswordHasher
import os
import sys

# Add the project root directory to the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plantask.models.base import Base
from plantask.models.user import User

ph = PasswordHasher()

# Database URL for the testing environment
TESTING_DATABASE_URL = "postgresql://postgres:DRbfLrlvWYCYCULVimbRZxufXbujGHaK@trolley.proxy.rlwy.net:35649/railway"

@pytest.fixture(scope="function")
def db_session():
    # Setup the database session and engine for testing
    engine = create_engine(TESTING_DATABASE_URL)
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    session = TestingSession()
    try:
        yield session
    finally:
        session.rollback()
        # Delete all rows from all tables in reverse order
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()

# Function to create a user and add to the database
def create_user(session, username, first_name, last_name, email, password, permission):
    hashed_password = ph.hash(password)
    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hashed_password,
        permission=permission
    )
    session.add(user)
    session.commit()
    return user

# Function to retrieve a user by their username
def get_user_by_username(session, username):
    return session.query(User).filter_by(username=username).first()


class TestAdminPrivileges:

    # Test to insert users with various parameters
    @pytest.mark.parametrize("username, first_name, last_name, email, password, permission", [
        (f"user{i}", f"First{i}", f"Last{i}", f"user{i}@example.com", f"pass{i}", "user") for i in range(10)
    ])
    def test_insert_user(self, db_session, username, first_name, last_name, email, password, permission):
        user = create_user(db_session, username, first_name, last_name, email, password, permission)
        retrieved = get_user_by_username(db_session, username)
        # Validate if the user was correctly added and password is hashed properly
        assert retrieved is not None
        assert retrieved.username == username
        assert retrieved.first_name == first_name
        assert retrieved.last_name == last_name
        assert retrieved.email == email
        assert ph.verify(retrieved.password, password)
        assert retrieved.permission == permission

    # Test user insertion with missing required fields (expecting IntegrityError)
    def test_insert_user_with_missing_fields(self, db_session):
        user = User(
            username="missing_fields_user",
            first_name="Missing",
            last_name="Fields",
            email=None,
            password=None,
            permission="User"
        )
        db_session.add(user)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
        # Verify user was not created
        assert get_user_by_username(db_session, "missing_fields_user") is None

    # Test updating user information (name and email)
    @pytest.mark.parametrize("original_name,new_name,new_email", [
        (f"user{i}", f"Updated{i}", f"updated{i}@example.com") for i in range(10)
    ])
    def test_update_user(self, db_session, original_name, new_name, new_email):
        create_user(db_session, original_name, "Old", "Name", f"{original_name}@example.com", "pass", "user")
        user = get_user_by_username(db_session, original_name)
        user.first_name = new_name
        user.email = new_email
        db_session.commit()
        # Verify if the user information was updated correctly
        updated = get_user_by_username(db_session, original_name)
        assert updated.first_name == new_name
        assert updated.email == new_email

    # Test retrieving a user by their username
    @pytest.mark.parametrize("username", [f"getuser{i}" for i in range(10)])
    def test_get_user(self, db_session, username):
        create_user(db_session, username, "Name", "Last", f"{username}@example.com", "pass", "user")
        retrieved = get_user_by_username(db_session, username)
        # Verify if the user is retrieved correctly
        assert retrieved is not None
        assert retrieved.username == username

    # Test deleting a user from the database
    @pytest.mark.parametrize("username", [f"deleteuser{i}" for i in range(10)])
    def test_delete_user(self, db_session, username):
        create_user(db_session, username, "Del", "User", f"{username}@example.com", "pass", "user")
        user = get_user_by_username(db_session, username)
        db_session.delete(user)
        db_session.commit()
        # Verify if the user was deleted successfully
        assert get_user_by_username(db_session, username) is None

    # Test promoting a user from "user" to "admin" permission level
    @pytest.mark.parametrize("username", [f"promote{i}" for i in range(10)])
    def test_promote_user(self, db_session, username):
        create_user(db_session, username, "Promote", "User", f"{username}@example.com", "pass", "user")
        user = get_user_by_username(db_session, username)
        user.permission = "admin"
        db_session.commit()
        # Verify if the user was successfully promoted
        assert get_user_by_username(db_session, username).permission == "admin"

    # Test demoting a user from "admin" to "user" permission level
    @pytest.mark.parametrize("username", [f"demote{i}" for i in range(10)])
    def test_demote_user(self, db_session, username):
        create_user(db_session, username, "Demote", "User", f"{username}@example.com", "pass", "admin")
        user = get_user_by_username(db_session, username)
        user.permission = "user"
        db_session.commit()
        # Verify if the user was successfully demoted
        assert get_user_by_username(db_session, username).permission == "user"


class TestNonAdminPrivileges:
    @allure.title("Test normal login by creating a user in the database")
    def test_normalLogin(self, db_session): 
        with allure.step("Create user and save it in the database"):
            hashed_password = ph.hash("user1pass")
            user = User(
                username="user1",
                first_name="Alice",
                last_name="Smith",
                email="alice.smith@example.com",
                password=hashed_password,
                permission="user"
            )
            db_session.add(user)
            db_session.commit()

        with allure.step("Query user and verify fields"):
            user = db_session.query(User).filter_by(username="user1").first()
            # Verify if the user details are correct after retrieval
            assert user is not None
            assert user.username == "user1"
            assert user.first_name == "Alice"
            assert user.last_name == "Smith"
            assert user.email == "alice.smith@example.com"
            assert ph.verify(user.password, "user1pass")
            assert user.permission == "user"
