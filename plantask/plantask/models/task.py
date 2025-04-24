from sqlalchemy import(
    Column, 
    Integer, 
    String, 
    Text, 
    DateTime, 
    ForeignKey, 
    Float
)
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.dialects.postgresql import ENUM

task_status = ('assigned', 'in_progress', 'under_review', 'completed')

task_status_enum = ENUM(*task_status, name = 'task_status')

class Task(Base):
    __tablename__ = 'tasks'

    # Primary key for the task
    id = Column(Integer, primary_key=True)
    # Foreign key linking to the 'projects' table
    project_id = Column(ForeignKey('projects.id'), nullable=False)
    # Title of the task (cannot be null)
    task_title = Column(String, nullable=False)
    # Description of the task (cannot be null)
    task_description = Column(Text, nullable=False)
    # Percentage of completion of the task (cannot be null)
    percentage_complete = Column(Float, nullable=False)
    # Date and time when the task was created (cannot be null)
    date_created = Column(DateTime, nullable=False)
    # Due date for the task (cannot be null)
    due_date = Column(DateTime, nullable=False)
    # Status of the task (cannot be null)
    status = Column(task_status_enum, nullable=False)

    # Relationship with the 'Project' model
    project = relationship('Project')

    def __repr__(self) -> str:
        # Custom string representation for the Task class
        return f"<Task(id={self.id}, task_title='{self.task_title}', task_description='{self.task_description}', percentage_complete={self.percentage_complete}, date_created={self.date_created}, due_date={self.due_date}, status='{self.status}')>"

class TaskComment(Base):
    __tablename__ = 'task_comments'

    # Primary key for the task comment
    id = Column(Integer, primary_key=True)
    # Foreign key linking to the 'users' table
    user_id = Column(ForeignKey('users.id'), nullable=False)
    # Foreign key linking to the 'tasks' table
    task_id = Column(ForeignKey('tasks.id'), nullable=False)
    # Time when the comment was posted (cannot be null)
    time_posted = Column(DateTime, nullable=False)
    # Content of the comment (cannot be null)
    content = Column(Text, nullable=False)

    # Relationship with the 'Task' and 'User' models
    task = relationship('Task')
    user = relationship('User')

    def __repr__(self) -> str:
        # Custom string representation for the TaskComment class
        return f"<TaskComment(id={self.id}, user_id={self.user_id}, task_id={self.task_id}, time_posted={self.time_posted}, content='{self.content}')>"
    
class TasksFile(Base):
    __tablename__ = 'tasks_files'

    # Primary key for the task file
    id = Column(Integer, primary_key=True)
    # Foreign key linking to the 'tasks' table
    tasks_id = Column(ForeignKey('tasks.id'), nullable=False)
    # Foreign key linking to the 'files' table
    files_id = Column(ForeignKey('files.id'), nullable=False)

    # Relationship with the 'File' and 'Task' models
    files = relationship('File')
    tasks = relationship('Task')

    def __repr__(self) -> str:
        # Custom string representation for the TasksFile class
        return f"<TasksFile(id={self.id}, tasks_id={self.tasks_id}, files_id={self.files_id})>"

class TaskCommentsFile(Base):
    __tablename__ = 'task_comments_files'

    # Primary key for the task comment file
    id = Column(Integer, primary_key=True)
    # Foreign key linking to the 'task_comments' table
    task_comments_id = Column(ForeignKey('task_comments.id'), nullable=False)
    # Foreign key linking to the 'files' table
    files_id = Column(ForeignKey('files.id'), nullable=False)

    # Relationship with the 'File' and 'TaskComment' models
    files = relationship('File')
    task_comments = relationship('TaskComment')

    def __repr__(self) -> str:
        # Custom string representation for the TaskCommentsFile class
        return f"<TaskCommentsFile(id={self.id}, task_comments_id={self.task_comments_id}, files_id={self.files_id})>"
