from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.dialects.postgresql import ENUM

user_roles = ('admin','project_manager','member','observer')

user_roles_enum = ENUM(*user_roles, name = 'user_roles')

class Project(Base):
    __tablename__ = 'projects'

    # Primary key of the project
    id = Column(Integer, primary_key=True)
    # Name of the project (cannot be null)
    name = Column(String, nullable=False)
    # Description of the project (cannot be null)
    description = Column(Text, nullable=False)
    # Date and time when the project was created (cannot be null)
    creation_datetime = Column(DateTime, nullable=False)

    # Define the relationship with the ProjectsUser model (one-to-many relationship)

    # A project can have many users associated with it
    users = relationship('ProjectsUser', back_populates='project', cascade="all, delete-orphan")

    # Project model:
    tasks = relationship('Task', back_populates='project')
    labels = relationship('Label', back_populates='project')
    notifications = relationship('Notification', back_populates='project')
    activity_logs = relationship('ActivityLog', back_populates='project')
    #personal_chats = relationship('PersonalChat', back_populates='project')


    def __repr__(self):
        # Custom string representation for the Project class
        return f"<Project(id={self.id}, name={self.name}, description={self.description[:20]}, created_at={self.creation_datetime})>"


class ProjectsUser(Base):
    __tablename__ = 'projects_users'

    # Primary key for the project-user association
    id = Column(Integer, primary_key=True)
    # Foreign key linking to the Project table (project ID)
    project_id = Column(ForeignKey('projects.id'), nullable=False)
    # Foreign key linking to the User table (user ID)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    # Role of the user in the project (cannot be null)
    role = Column(user_roles_enum, nullable=False)

    # Relationships with the Project and User tables (many-to-one relationship)
    project = relationship('Project', back_populates='users')
    user = relationship('User', back_populates='projects')
    
    # Relationship to the ProjectsUsersMicrotask model (one-to-many relationship)
    microtasks_link = relationship('ProjectsUsersMicrotask', back_populates='projects_users', cascade="all, delete-orphan")
    user = relationship('User', back_populates='projects_users')  # <-- Cambia 'projects' por 'projects_users'


    def __repr__(self):
        # Custom string representation for the ProjectsUser class
        return f"<ProjectsUser(id={self.id}, project_id={self.project_id}, user_id={self.user_id}, role={self.role})>"


class ProjectsUsersMicrotask(Base):
    __tablename__ = 'projects_users_microtasks'

    # Primary key for the projects_users_microtasks table
    id = Column(Integer, primary_key=True)
    # Foreign key linking to the ProjectsUsers table (projects_users ID)
    projects_users_id = Column(ForeignKey('projects_users.id'), nullable=False)
    # Foreign key linking to the Microtask table (microtask ID)
    microtasks_id = Column(ForeignKey('microtasks.id'), nullable=False)

    # Relationship to the Microtask model (many-to-one relationship)
    microtasks = relationship('Microtask', back_populates='users_link')
    # Relationship to the ProjectsUser model (many-to-one relationship)
    projects_users = relationship('ProjectsUser', back_populates='microtasks_link')

    def __repr__(self):
        # Custom string representation for the ProjectsUsersMicrotask class
        return f"<ProjectsUsersMicrotask(id={self.id}, projects_users_id={self.projects_users_id}, microtasks_id={self.microtasks_id})>"
