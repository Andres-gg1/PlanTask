from sqlalchemy import(
    Column, 
    Integer, 
    Text, 
    ForeignKey,
    String,
    Boolean
)
from sqlalchemy.orm import relationship
from .base import Base

class Template(Base):
    __tablename__ = 'templates'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    is_microtask = Column(Boolean, nullable=False)

    user = relationship('User')


class TemplatesFile(Base):
    __tablename__ = 'templates_files'

    id = Column(Integer, primary_key=True)
    templates_id = Column(ForeignKey('templates.id'), nullable=False)
    files_id = Column(ForeignKey('files.id'), nullable=False)

    files = relationship('File')
    templates = relationship('Template')