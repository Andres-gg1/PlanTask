from sqlalchemy import (
    Column, 
    Integer, 
    Text, 
    DateTime, 
    ForeignKey,
)

from sqlalchemy.orm import relationship
from .base import Base


class Notification(Base):
    __tablename__ = 'notifications'

    # Primary key for the notification
    id = Column(Integer, primary_key=True)

    # Foreign key linking to the user who receives the notification
    user_id = Column(ForeignKey('users.id'))

    # Foreign key linking to the related project (if applicable)
    project_id = Column(ForeignKey('projects.id'))

    # Content of the notification message
    message = Column(Text, nullable=False)

    # Timestamp when the notification was sent
    time_sent = Column(DateTime, nullable=False)

    # Relationship to access the associated project
    project = relationship('Project')

    # Relationship to access the associated user
    user = relationship('User')

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, project_id={self.project_id}, message={self.message}, time_sent={self.time_sent})>"