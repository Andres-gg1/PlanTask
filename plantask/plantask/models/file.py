from sqlalchemy import(
    Column, 
    Integer, 
    Text, 
    DateTime, 
)
from sqlalchemy.orm import relationship
from .base import Base

class File(Base):
    __tablename__ = 'files'

    # Primary key for the file
    id = Column(Integer, primary_key=True)
    # Name of the file (cannot be null)
    filename = Column(Text, nullable=False)
    # Extension of the file (cannot be null)
    extension = Column(Text, nullable=False)
    # Route or path where the file is stored (cannot be null)
    route = Column(Text, nullable=False)
    # Date and time when the file was created (cannot be null)
    creation_date = Column(DateTime, nullable=False)

    files_tasks = relationship('TasksFile', back_populates='files')
    files_templates = relationship('TemplatesFile', back_populates='files')
    files_chat_logs = relationship('ChatLogsFile', back_populates='files')
    files_microtasks = relationship('MicrotasksFile', back_populates='files')
    files_task_comments = relationship('TaskCommentsFile', back_populates='files')
    files_microtask_comments = relationship('MicrotaskCommentsFile', back_populates='files')
    activity_logs = relationship('ActivityLog', back_populates='file')
    group_chats = relationship('GroupChat', back_populates='image')


    def __repr__(self):
        return f"<File(id={self.id}, filename={self.filename}, extension={self.extension})>"
