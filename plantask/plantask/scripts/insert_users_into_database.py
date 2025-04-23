from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from argon2 import PasswordHasher
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plantask.models.user import User

# Configuración de la base de datos
DATABASE_URL = "postgresql://postgres:DRbfLrlvWYCYCULVimbRZxufXbujGHaK@trolley.proxy.rlwy.net:35649/railway"  # o tu URL de conexión a PostgreSQL/MySQL
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Hasher de contraseñas
psw_hasher = PasswordHasher()

# Lista de usuarios por crear
users_to_create = [
    {
        "username": "PLANTASK_ADMIN",
        "first_name": "System",
        "last_name": "Administrator",
        "email": "admin@kochcc.com",
        "password": "314PLANTASK_SECURE_SUPER_PASSWORD159",
        "permission": "admin"
    },
    {
        "username": "user1",
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice.smith@kochcc.com",
        "password": "user1pass",
        "permission": "user"
    },
    {
        "username": "user2",
        "first_name": "Bob",
        "last_name": "Johnson",
        "email": "bob.johnson@kochcc.com",
        "password": "user2pass",
        "permission": "user"
    },
    {
        "username": "user3",
        "first_name": "Carol",
        "last_name": "Williams",
        "email": "carol.williams@kochcc.com",
        "password": "user3pass",
        "permission": "user"
    },
    {
        "username": "user4",
        "first_name": "David",
        "last_name": "Brown",
        "email": "david.brown@kochcc.com",
        "password": "user4pass",
        "permission": "user"
    },
]

for user_data in users_to_create:
    existing_user = session.query(User).filter(
        or_(User.username == user_data["username"], User.email == user_data["email"])
    ).first()

    if existing_user:
        print(f"El usuario '{user_data['username']}' ya existe.")
        continue

    try:
        hashed_password = psw_hasher.hash(user_data["password"])
        new_user = User(
            username=user_data["username"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            password=hashed_password,
            permission=user_data["permission"]
        )
        session.add(new_user)
        print(f"Usuario '{user_data['username']}' creado exitosamente.")
    except Exception as e:
        print(f"Error al crear el usuario '{user_data['username']}': {e}")

session.commit()
session.close()