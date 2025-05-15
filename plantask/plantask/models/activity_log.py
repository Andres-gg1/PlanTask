from sqlalchemy import (
    Column,
    BigInteger,
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.dialects.postgresql import ENUM

log_actions = (
    # Project Actions
    'project_added',
    'project_removed',
    'project_added_image',
    'project_removed_image',
    'project_edited_title',
    'project_edited_description',
    'project_added_user',
    'project_removed_user',
    'project_added_label',
    'project_removed_label',
    'project_user_assigned_label',
    'project_user_removed_label',
    'project_task_assigned_label',
    'project_task_removed_label',

    # Task Actions
    'task_created',
    'task_removed',
    'task_edited_title',
    'task_edited_description',
    'task_edited_status',
    'task_edited_duedate',
    'task_added_file',
    'task_removed_file',
    'task_added_comment',
    'task_removed_comment',
    'task_comment_added_file',
    'task_comment_removed_file',

    # Microtask Actions
    'microtask_created',
    'microtask_removed',
    'microtask_edited_name',
    'microtask_edited_description',
    'microtask_edited_percentage',
    'microtask_edited_status',
    'microtask_assigned_user',
    'microtask_removed_user',
    'microtask_added_comment',
    'microtask_removed_comment',
    'microtask_comment_added_file',
    'microtask_comment_removed_file',
    'microtask_added_file',
    'microtask_removed_file',
    'microtask_added_duedate',
    'microtask_removed_duedate',

    # Group Chat Actions
    'message_group_created',
    'message_group_deleted',
    'message_group_edited_name',
    'message_group_added_image',
    'message_group_removed_image',
    'message_group_added_member',
    'message_group_removed_member',
    'message_group_added_description',
    'message_group_edited_description',
    'message_group_removed_description',

    # Login Actions
    'login_several_failed_attempts',
    'login_user_successful',

    # Registration Actions
    'registration_new_user'
)

log_actions_enum = ENUM(*log_actions, name="log_actions")


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
    action = Column(log_actions_enum, nullable=False)

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