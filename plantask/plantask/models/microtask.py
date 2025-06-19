from sqlalchemy import(
    Column, 
    Integer, 
    String, 
    Text, 
    DateTime, 
    ForeignKey, 
    Float,
    Boolean
)
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.dialects.postgresql import ENUM

microtask_status = ('undone', 'under_review', 'approved')

microtask_status_enum = ENUM(*microtask_status, name = 'microtask_status')

class Microtask(Base):
    __tablename__ = 'microtasks'

    # Primary key for the microtask
    id = Column(Integer, primary_key=True) 
    # Foreign key linking to the 'tasks' table
    task_id = Column(ForeignKey('tasks.id'), nullable=False)
    # Name of the microtask (cannot be null)
    name = Column(String, nullable=False)
    # Description of the microtask (cannot be null)
    description = Column(Text, nullable=False)
    # Percentage of completion of the microtask (cannot be null)
    percentage_complete = Column(Float, nullable=False)
    # Date and time when the microtask was created (cannot be null)
    date_created = Column(DateTime, nullable=False)
    # Status of the microtask (cannot be null)
    status = Column(microtask_status_enum, nullable=False)
    # Due date for the microtask
    due_date = Column(DateTime)
    # Active boolean
    active = Column(Boolean, nullable = False, default = True)

    # Relationship with the 'Task' model
    task = relationship('Task')
    users_link = relationship('ProjectsUsersMicrotask', back_populates='microtasks', cascade="all, delete-orphan")
    comments = relationship('MicrotaskComment', back_populates='microtask', cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Microtask(id={self.id}, name={self.name}, task_id={self.task_id})>"

class MicrotaskComment(Base):
    __tablename__ = 'microtask_comments'

    # Primary key for the microtask comment
    id = Column(Integer, primary_key=True)
    # Foreign key linking to the 'users' table
    user_id = Column(ForeignKey('users.id'), nullable=False)
    # Foreign key linking to the 'microtasks' table
    microtask_id = Column(ForeignKey('microtasks.id'), nullable=False)
    # Time when the comment was posted (cannot be null)
    time_posted = Column(DateTime, nullable=False)
    # Content of the comment (cannot be null)
    content = Column(Text, nullable=False)

    # Relationship with the 'Microtask' and 'User' models
    microtask = relationship('Microtask')
    user = relationship('User')

    def __repr__(self):
        return f"<MicrotaskComment(id={self.id}, user_id={self.user_id}, microtask_id={self.microtask_id})>"

class MicrotasksFile(Base):
    __tablename__ = 'microtasks_files'

    # Primary key for the microtask file
    id = Column(Integer, primary_key=True)
    # Foreign key linking to the 'microtasks' table
    microtasks_id = Column(ForeignKey('microtasks.id'), nullable=False)
    # Foreign key linking to the 'files' table
    files_id = Column(ForeignKey('files.id'), nullable=False)

    # Relationship with the 'File' and 'Microtask' models
    files = relationship('File')
    microtasks = relationship('Microtask')

    def __repr__(self):
        return f"<MicrotasksFile(id={self.id}, microtasks_id={self.microtasks_id}, files_id={self.files_id})>"

class MicrotaskCommentsFile(Base):
    __tablename__ = 'microtask_comments_files'

    # Primary key for the microtask comment file
    id = Column(Integer, primary_key=True)
    # Foreign key linking to the 'microtask_comments' table
    microtask_comments_id = Column(ForeignKey('microtask_comments.id'), nullable=False)
    # Foreign key linking to the 'files' table
    files_id = Column(ForeignKey('files.id'), nullable=False)

    # Relationship with the 'File' and 'MicrotaskComment' models
    files = relationship('File')
    microtask_comments = relationship('MicrotaskComment')

    def __repr__(self):
        return f"<MicrotaskCommentsFile(id={self.id}, microtask_comments_id={self.microtask_comments_id}, files_id={self.files_id})>"
