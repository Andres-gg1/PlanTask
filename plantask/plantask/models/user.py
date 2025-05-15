from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.dialects.postgresql import ENUM

permissions = ('admin', 'user', 'pm')

permissions_enum = ENUM(*permissions, name='permissions')

class User(Base):
    """
    Model that represents a user within the system.
    """
    __tablename__ = 'users'

    # Primary key of the user
    id: int = Column(Integer, primary_key=True)
    # Username of the user (cannot be null)
    username: str = Column(String, nullable=False)
    # First name of the user (cannot be null)
    first_name: str = Column(String, nullable=False)
    # Last name of the user (cannot be null)
    last_name: str = Column(String, nullable=False)
    # Email of the user (cannot be null)
    email: str = Column(String, nullable=False)
    # Password of the user (cannot be null)
    password: str = Column(String, nullable=False)
    # Permissions assigned to the user (cannot be null). either "admin" or "user", used for limiting access to admin functions. Uses enum type
    permission: str = Column(permissions_enum, nullable=False)

    task_comments = relationship('TaskComment', back_populates='user')
    microtask_comments = relationship('MicrotaskComment', back_populates='user')
    templates = relationship('Template', back_populates='user')
    notifications = relationship('Notification', back_populates='user')
    activity_logs = relationship('ActivityLog', back_populates='user', foreign_keys='ActivityLog.user_id')
    object_activity_logs = relationship('ActivityLog', back_populates='object_user', foreign_keys='ActivityLog.object_user_id')
    # En el modelo User:
    projects_users = relationship('ProjectsUser', back_populates='user')


    def __repr__(self) -> str:
        # Custom string representation for the User class
        return (
            f"<User(id={self.id}, username='{self.username}', first_name='{self.first_name}', "
            f"last_name='{self.last_name}', email='{self.email}', 'permission='{self.permission}')>"
        )
