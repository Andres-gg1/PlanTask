from sqlalchemy import (
    Column,
    BigInteger,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from .base import Base


class ActivityLog(Base):
    __tablename__ = 'activity_log'

    # Unique identifier for each log entry
    id = Column(BigInteger, primary_key=True)

    # The user who performed the action
    user_id = Column(ForeignKey('users.id'), nullable=False)

    # (Optional) The user who was the target of the action
    object_user_id = Column(ForeignKey('users.id'))

    # (Optional) Related project
    project_id = Column(ForeignKey('projects.id'))

    # (Optional) Related task
    task_id = Column(ForeignKey('tasks.id'))

    # (Optional) Related microtask
    microtask_id = Column(ForeignKey('microtasks.id'))

    # (Optional) Related file
    file_id = Column(ForeignKey('files.id'))

    # (Optional) Related group chat
    groupchat_id = Column(ForeignKey('group_chats.id'))

    # Timestamp of when the action occurred
    timestamp = Column(DateTime, nullable=False)

    # Description of the action performed (e.g., "created", "edited", "deleted")
    action = Column(Text, nullable=False)

    # Context or category of the action
    context = Column(Text, nullable=False)

    # Detailed info about the changes made (optional)
    changes = Column(Text)

    # Relationships to associated entities
    file = relationship('File')
    groupchat = relationship('GroupChat')
    microtask = relationship('Microtask')
    object_user = relationship('User', primaryjoin='ActivityLog.object_user_id == User.id')
    project = relationship('Project')
    task = relationship('Task')
    user = relationship('User', primaryjoin='ActivityLog.user_id == User.id')

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, action={self.action}, timestamp={self.timestamp})>"