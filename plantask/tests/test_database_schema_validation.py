# test_schema_validation.py

from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plantask.models.base import Base

import pytest 
import allure

#BE SURE TO RUN PYTEST <route> -v TO SEE THE PRINT FUNCTION OUTPUT

#Database URL for test environment
# This URL is for a PostgreSQL testing database hosted on Railway. Use this to run tests without affecting the production database.
TESTING_DATABASE_URL = "postgresql://postgres:DRbfLrlvWYCYCULVimbRZxufXbujGHaK@trolley.proxy.rlwy.net:35649/railway"

# This URL is for a PostgreSQL database hosted on Railway. Use this to run the application in production.
DATABASE_URL = "postgresql://postgres:hqDGUoMpypystmdWLOYHdzOMrABijDKi@hopper.proxy.rlwy.net:32534/railway"

DATABASES_URL = [
    DATABASE_URL,
    TESTING_DATABASE_URL
]


# --------------------------- TESTING DATABASE CONNECTION --------------------------- #
# This test suite checks if the database connection is established successfully.

@allure.title("Test if the database connection is established successfully")
@allure.description("""
This test checks if the database connection is established successfully.
It attempts to connect to the database using the provided database URL.
If the connection is successful, it returns a success message.
If the connection fails, it raises an assertion error.
""")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("db_url", DATABASES_URL)
def test_databases_connection(db_url):
    try:
        with allure.step(f"Create SQLAlchemy engine for database URL: {db_url}"):
            engine = create_engine(db_url)

        with allure.step("Connect to the database and execute test query"):
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1")).fetchone()
                assert result is not None and result[0] == 1, "Database connection failed!"
    
    except SQLAlchemyError as e:
        allure.attach(str(e), name="Database Error", attachment_type=allure.attachment_type.TEXT)
        pytest.fail(f"Could not connect to database: {e}")
            

# --------------------------- TESTING DATABASE SCHEMA --------------------------- #
# This test suite checks if the database schema matches the SQLAlchemy models defined in the application.

@allure.title("Test if all SQLAlchemy models are present in both databases, PROD and TEST")
@allure.description("""
This test checks if all SQLAlchemy models are present in the actual database.
It compares the tables defined in the SQLAlchemy models with the tables present in the database.
If there are any discrepancies, it raises an assertion error.
""")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("db_url", DATABASES_URL)
def test_model_and_db_tables_match(db_url):
    with allure.step(f"Create SQLAlchemy engine for database URL: {db_url}"):
        engine = create_engine(db_url)

    with allure.step("Inspect database schema and retrieve table names excluding 'alembic_version'"): 
        # Use the SQLAlchemy inspector to get the table names from the database
        inspector = inspect(engine)
        db_tables = set(inspector.get_table_names()) # Get the table names from the database
        model_tables = set(Base.metadata.tables.keys()) # Get the table names from the SQLAlchemy models

        db_tables.discard('alembic_version') # Remove 'alembic_version' from the database tables
        model_tables.discard('alembic_version') # Remove 'alembic_version' from the model tables

    with allure.step("Compare model tables with database tables"):
        missing_in_db = model_tables.difference(db_tables) # Tables defined in models but missing in DB
        extra_in_db = db_tables.difference(model_tables) # Tables in DB but not defined in models

        if missing_in_db:
            allure.attach(str(missing_in_db), name="Missing Tables in DB", attachment_type=allure.attachment_type.TEXT) # Attach missing tables to Allure report
        if extra_in_db:
            allure.attach(str(extra_in_db), name="Extra Tables in DB", attachment_type=allure.attachment_type.TEXT) # Attach extra tables to Allure report

    with allure.step("Assert that model and database tables match"): 
        assert not missing_in_db, f"Tables defined in models but missing in DB:\n{missing_in_db}" # Tables defined in models but missing in DB
        assert not extra_in_db, f"Tables in DB but not defined in models:\n{extra_in_db}" # Tables in DB but not defined in models



# --------------------------- TESTING DATABASE FOREIGN KEYS --------------------------- #
# This test suite checks if the foreign keys in the database match the foreign keys defined in the SQLAlchemy models.

@allure.title("Test if foreign keys in both DBs (PROD and TEST) match model definitions")
@allure.description("""
This test checks if the foreign keys defined in the SQLAlchemy models match the foreign keys present in the actual database.
It compares the foreign keys defined in the SQLAlchemy models with the foreign keys present in the database.
If there are any discrepancies, it raises an assertion error.
""")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("db_url", DATABASES_URL)
def test_foreign_keys_match(db_url):
    """Ensure that foreign keys in DB match model definitions."""

    with allure.step(f"Create SQLAlchemy engine for database URL: {db_url}"):
        engine = create_engine(db_url)  # Create a new engine instance for the test database

    with allure.step("Inspect database schema and retrieve foreign keys information"):
        inspector = inspect(engine)
        metadata = Base.metadata

    for table_name in metadata.tables:
        model_table = metadata.tables[table_name]
        db_fks = inspector.get_foreign_keys(table_name)

        db_fk_set = {
            (tuple(fk['constrained_columns']), fk['referred_table'], tuple(fk['referred_columns']))
            for fk in db_fks
        }

        model_fk_set = {
            (tuple([fk.parent.name]), fk.column.table.name, tuple([fk.column.name]))
            for fk in model_table.foreign_keys
        }

        with allure.step(f"Compare foreign keys for table '{table_name}'"):
            if model_fk_set != db_fk_set:
                # Attach the mismatch details to Allure report
                allure.attach(
                    f"Model Foreign Keys: {model_fk_set}\nDB Foreign Keys: {db_fk_set}",
                    name=f"Foreign Keys Mismatch in Table '{table_name}'",
                    attachment_type=allure.attachment_type.TEXT
                )

        with allure.step(f"Assert that foreign keys match for table '{table_name}'"):
            assert model_fk_set == db_fk_set, f"Foreign keys mismatch in table '{table_name}':\n\nModel: {model_fk_set}\nDB: {db_fk_set}"