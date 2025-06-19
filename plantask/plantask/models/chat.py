from sqlalchemy import (
    Column, 
    Integer, 
    Text, 
    DateTime, 
    ForeignKey,
    Table
)
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.dialects.postgresql import ENUM

msg_state = ('sent','delivered','read')

msg_state_enum = ENUM(*msg_state, name='msg_state')

groupchat_users = Table(
    'groupchat_users',
    Base.metadata,
    Column('groupchat_id', ForeignKey('group_chats.id'), primary_key=True),
    Column('user_id', ForeignKey('users.id'), primary_key=True)
)

class GroupChat(Base):
    __tablename__ = 'group_chats'

    # Primary key for the group chat
    id = Column(Integer, primary_key=True)
    # Foreign key pointing to the image file (optional)
    image_id = Column(ForeignKey('files.id'))
    # Name of the group chat (cannot be null)
    chat_name = Column(Text, nullable=False)
    # Date the group chat was created (cannot be null)
    creation_date = Column(DateTime, nullable=False)
    # Optional description for the group chat
    description = Column(Text)

    # Relationship to access the associated image file
    image = relationship('File')

    # Many-to-many relationship with User
    users = relationship('User', secondary=groupchat_users, back_populates='group_chats')

    def __repr__(self):
        return f"<GroupChat(id={self.id}, chat_name={self.chat_name})>"


class PersonalChat(Base):
    __tablename__ = 'personal_chats'

    # Primary key for the personal chat
    id = Column(Integer, primary_key=True)
    # Foreign key for the first user in the chat (cannot be null)
    user1_id = Column(ForeignKey('users.id'), nullable=False)
    # Foreign key for the second user in the chat (cannot be null)
    user2_id = Column(ForeignKey('users.id'), nullable=False)
    # Foreign key linking to the 'projects' table (if required)
    project_id = Column(ForeignKey('projects.id'), nullable=True)  # Si 'nullable=True' lo puedes dejar opcional

    # Relationships to users
    user1 = relationship('User', primaryjoin='PersonalChat.user1_id == User.id')
    user2 = relationship('User', primaryjoin='PersonalChat.user2_id == User.id')

    # Relationship to the project
    project = relationship('Project', back_populates='personal_chats')


    def __repr__(self):
        return f"<PersonalChat(id={self.id}, user1_id={self.user1_id}, user2_id={self.user2_id})>"

class ChatLog(Base):
    __tablename__ = 'chat_logs'

    # Primary key for the chat message
    id = Column(Integer, primary_key=True)
    # Optional foreign key if the message belongs to a personal chat
    perschat_id = Column(ForeignKey('personal_chats.id'))
    # Optional foreign key if the message belongs to a group chat
    groupchat_id = Column(ForeignKey('group_chats.id'))
    # Foreign key for the sender of the message (cannot be null)
    sender_id = Column(ForeignKey('users.id'), nullable=False)
    # Date and time the message was sent (cannot be null)
    date_sent = Column(DateTime, nullable=False)
    # State of the message (e.g., sent, delivered, read)
    state = Column(msg_state_enum, nullable=False)
    # Content of the message (optional)
    message_cont = Column(Text)

    # Relationships to access associated entities
    groupchat = relationship('GroupChat')
    perschat = relationship('PersonalChat')
    sender = relationship('User')

    def __repr__(self):
        return f"<ChatLog(id={self.id}, sender_id={self.sender_id}, date_sent={self.date_sent})>"


class ChatLogsFile(Base):
    __tablename__ = 'chat_logs_files'

    # Primary key for the attachment record
    id = Column(Integer, primary_key=True)
    # Foreign key linking to the chat log (cannot be null)
    chat_logs_id = Column(ForeignKey('chat_logs.id'), nullable=False)
    # Foreign key linking to the attached file (cannot be null)
    files_id = Column(ForeignKey('files.id'), nullable=False)

    # Relationship to access the associated chat log
    chat_logs = relationship('ChatLog')
    files = relationship('File', back_populates='files_chat_logs')

    def __repr__(self):
        return f"<ChatLogsFile(id={self.id}, chat_logs_id={self.chat_logs_id}, files_id={self.files_id})>"