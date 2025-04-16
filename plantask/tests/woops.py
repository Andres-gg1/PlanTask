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

engine = create_engine(TESTING_DATABASE_URL)
Session = scoped_session(sessionmaker(bind=engine))
session = Session()

psw_hasher = argon2.PasswordHasher()

user = User(
        username="__PLAN_ADMIN_TASK__",
        password=password,
        permission=permission
    )
session.add(user)
session.flush()