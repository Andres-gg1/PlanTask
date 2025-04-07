from sqlalchemy import (
    Column, 
    Integer, 
    Text, 
    DateTime, 
    ForeignKey,
)
from sqlalchemy.orm import relationship
from .base import Base

class Label(Base):
    __tablename__ = 'labels'

    # Primary key for the label
    id = Column(Integer, primary_key=True)
    # Foreign key linking the label to a specific project
    project_id = Column(ForeignKey('projects.id'), nullable=False)
    # Name of the label (e.g., "urgent", "review")
    label_name = Column(Text, nullable=False)
    # Color associated with the label in HEX format (e.g., "#FF5733")
    label_hex_color = Column(Text, nullable=False)

    # Relationship to access the associated project
    project = relationship('Project')

    def __repr__(self):
        return f"<Label(id={self.id}, project_id={self.project_id}, label_name={self.label_name})>"


class LabelsTask(Base):
    __tablename__ = 'labels_tasks'

    # Primary key for the link between a label and a task
    id = Column(Integer, primary_key=True)
    # Foreign key linking to a label
    labels_id = Column(ForeignKey('labels.id'), nullable=False)
    # Foreign key linking to a task
    tasks_id = Column(ForeignKey('tasks.id'), nullable=False)

    # Relationships to access the associated label and task
    labels = relationship('Label')
    tasks = relationship('Task')

    def __repr__(self):
        return f"<LabelsTask(id={self.id}, labels_id={self.labels_id}, tasks_id={self.tasks_id})>"


class LabelsTemplate(Base):
    __tablename__ = 'labels_templates'

    # Primary key for the link between a label and a template
    id = Column(Integer, primary_key=True)
    # Foreign key linking to a label
    labels_id = Column(ForeignKey('labels.id'), nullable=False)
    # Foreign key linking to a template
    templates_id = Column(ForeignKey('templates.id'), nullable=False)

    # Relationships to access the associated label and template
    labels = relationship('Label')
    templates = relationship('Template')

    def __repr__(self):
        return f"<LabelsTemplate(id={self.id}, labels_id={self.labels_id}, templates_id={self.templates_id})>"


class LabelsProjectsUser(Base):
    __tablename__ = 'labels_projects_users'

    # Primary key for the link between a label and a user-project association
    id = Column(Integer, primary_key=True)
    # Foreign key linking to a label
    labels_id = Column(ForeignKey('labels.id'), nullable=False)
    # Foreign key linking to a user assigned to a project
    projects_users_id = Column(ForeignKey('projects_users.id'), nullable=False)

    # Relationships to access the associated label and user-project record
    labels = relationship('Label')
    projects_users = relationship('ProjectsUser')

    def __repr__(self):
        return f"<LabelsProjectsUser(id={self.id}, labels_id={self.labels_id}, projects_users_id={self.projects_users_id})>"