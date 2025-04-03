# coding: utf-8
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, server_default=text("nextval('files_id_seq'::regclass)"))
    filename = Column(Text, nullable=False)
    extension = Column(Text, nullable=False)
    route = Column(Text, nullable=False)
    creation_date = Column(DateTime, nullable=False)
    last_modified = Column(DateTime, nullable=False)


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, server_default=text("nextval('projects_id_seq'::regclass)"))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    creation_datetime = Column(DateTime, nullable=False)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, server_default=text("nextval('users_id_seq'::regclass)"))
    username = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    permission = Column(Text, nullable=False)


class GroupChat(Base):
    __tablename__ = 'group_chats'

    id = Column(Integer, primary_key=True, server_default=text("nextval('group_chats_id_seq'::regclass)"))
    image_id = Column(ForeignKey('files.id'))
    chat_name = Column(Text, nullable=False)
    creation_date = Column(DateTime, nullable=False)
    description = Column(Text)

    image = relationship('File')


class Label(Base):
    __tablename__ = 'labels'

    id = Column(Integer, primary_key=True, server_default=text("nextval('labels_id_seq'::regclass)"))
    project_id = Column(ForeignKey('projects.id'), nullable=False)
    label_name = Column(Text, nullable=False)
    label_hex_color = Column(Text, nullable=False)

    project = relationship('Project')


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, server_default=text("nextval('notifications_id_seq'::regclass)"))
    user_id = Column(ForeignKey('users.id'))
    project_id = Column(ForeignKey('projects.id'))
    message = Column(Text, nullable=False)
    time_sent = Column(DateTime, nullable=False)

    project = relationship('Project')
    user = relationship('User')


class PersonalChat(Base):
    __tablename__ = 'personal_chats'

    id = Column(Integer, primary_key=True, server_default=text("nextval('personal_chats_id_seq'::regclass)"))
    user1_id = Column(ForeignKey('users.id'), nullable=False)
    user2_id = Column(ForeignKey('users.id'), nullable=False)

    user1 = relationship('User', primaryjoin='PersonalChat.user1_id == User.id')
    user2 = relationship('User', primaryjoin='PersonalChat.user2_id == User.id')


class ProjectsUser(Base):
    __tablename__ = 'projects_users'

    id = Column(Integer, primary_key=True, server_default=text("nextval('projects_users_id_seq'::regclass)"))
    project_id = Column(ForeignKey('projects.id'), nullable=False)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    labels = Column(Text)
    role = Column(Text, nullable=False)

    project = relationship('Project')
    user = relationship('User')


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, server_default=text("nextval('tasks_id_seq'::regclass)"))
    project_id = Column(ForeignKey('projects.id'), nullable=False)
    task_title = Column(String, nullable=False)
    task_description = Column(Text, nullable=False)
    percentage_complete = Column(Float, nullable=False, server_default=text("0"))
    date_created = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(Text, nullable=False)

    project = relationship('Project')


class Template(Base):
    __tablename__ = 'templates'

    id = Column(Integer, primary_key=True, server_default=text("nextval('templates_id_seq'::regclass)"))
    user_id = Column(ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    is_microtask = Column(Boolean, nullable=False)

    user = relationship('User')


class ChatLog(Base):
    __tablename__ = 'chat_logs'

    id = Column(Integer, primary_key=True, server_default=text("nextval('chat_logs_id_seq'::regclass)"))
    perschat_id = Column(ForeignKey('personal_chats.id'))
    groupchat_id = Column(ForeignKey('group_chats.id'))
    sender_id = Column(ForeignKey('users.id'), nullable=False)
    date_sent = Column(DateTime, nullable=False)
    state = Column(Text, nullable=False)
    message_cont = Column(Text)

    groupchat = relationship('GroupChat')
    perschat = relationship('PersonalChat')
    sender = relationship('User')


class LabelsProjectsUser(Base):
    __tablename__ = 'labels_projects_users'

    id = Column(Integer, primary_key=True, server_default=text("nextval('labels_projects_users_id_seq'::regclass)"))
    labels_id = Column(ForeignKey('labels.id'), nullable=False, server_default=text("nextval('labels_projects_users_labels_id_seq'::regclass)"))
    projects_users_id = Column(ForeignKey('projects_users.id'), nullable=False, server_default=text("nextval('labels_projects_users_projects_users_id_seq'::regclass)"))

    labels = relationship('Label')
    projects_users = relationship('ProjectsUser')


class LabelsTask(Base):
    __tablename__ = 'labels_tasks'

    id = Column(Integer, primary_key=True, server_default=text("nextval('labels_tasks_id_seq'::regclass)"))
    labels_id = Column(ForeignKey('labels.id'), nullable=False, server_default=text("nextval('labels_tasks_labels_id_seq'::regclass)"))
    tasks_id = Column(ForeignKey('tasks.id'), nullable=False, server_default=text("nextval('labels_tasks_tasks_id_seq'::regclass)"))

    labels = relationship('Label')
    tasks = relationship('Task')


class LabelsTemplate(Base):
    __tablename__ = 'labels_templates'

    id = Column(Integer, primary_key=True, server_default=text("nextval('labels_templates_id_seq'::regclass)"))
    labels_id = Column(ForeignKey('labels.id'), nullable=False, server_default=text("nextval('labels_templates_labels_id_seq'::regclass)"))
    templates_id = Column(ForeignKey('templates.id'), nullable=False, server_default=text("nextval('labels_templates_templates_id_seq'::regclass)"))

    labels = relationship('Label')
    templates = relationship('Template')


class Microtask(Base):
    __tablename__ = 'microtasks'

    id = Column(Integer, primary_key=True, server_default=text("nextval('microtasks_id_seq'::regclass)"))
    task_id = Column(ForeignKey('tasks.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    percentage_complete = Column(Float, nullable=False, server_default=text("0"))
    date_created = Column(DateTime, nullable=False)
    status = Column(Text, nullable=False)
    due_date = Column(DateTime)

    task = relationship('Task')


class TaskComment(Base):
    __tablename__ = 'task_comments'

    id = Column(Integer, primary_key=True, server_default=text("nextval('task_comments_id_seq'::regclass)"))
    user_id = Column(ForeignKey('users.id'), nullable=False)
    task_id = Column(ForeignKey('tasks.id'), nullable=False)
    time_posted = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)

    task = relationship('Task')
    user = relationship('User')


class TasksFile(Base):
    __tablename__ = 'tasks_files'

    id = Column(Integer, primary_key=True, server_default=text("nextval('tasks_files_id_seq'::regclass)"))
    tasks_id = Column(ForeignKey('tasks.id'), nullable=False)
    files_id = Column(ForeignKey('files.id'), nullable=False)

    files = relationship('File')
    tasks = relationship('Task')


class TemplatesFile(Base):
    __tablename__ = 'templates_files'

    id = Column(Integer, primary_key=True, server_default=text("nextval('templates_files_id_seq'::regclass)"))
    templates_id = Column(ForeignKey('templates.id'), nullable=False)
    files_id = Column(ForeignKey('files.id'), nullable=False)

    files = relationship('File')
    templates = relationship('Template')


class ActivityLog(Base):
    __tablename__ = 'activity_log'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('activity_log_id_seq'::regclass)"))
    user_id = Column(ForeignKey('users.id'), nullable=False)
    object_user_id = Column(ForeignKey('users.id'))
    project_id = Column(ForeignKey('projects.id'))
    task_id = Column(ForeignKey('tasks.id'))
    microtask_id = Column(ForeignKey('microtasks.id'))
    file_id = Column(ForeignKey('files.id'))
    groupchat_id = Column(ForeignKey('group_chats.id'))
    timestamp = Column(DateTime, nullable=False)
    action = Column(Text, nullable=False)
    context = Column(Text, nullable=False)
    changes = Column(Text)

    file = relationship('File')
    groupchat = relationship('GroupChat')
    microtask = relationship('Microtask')
    object_user = relationship('User', primaryjoin='ActivityLog.object_user_id == User.id')
    project = relationship('Project')
    task = relationship('Task')
    user = relationship('User', primaryjoin='ActivityLog.user_id == User.id')


class ChatLogsFile(Base):
    __tablename__ = 'chat_logs_files'

    id = Column(Integer, primary_key=True, server_default=text("nextval('chat_logs_files_id_seq'::regclass)"))
    chat_logs_id = Column(ForeignKey('chat_logs.id'), nullable=False)
    files_id = Column(ForeignKey('files.id'), nullable=False)

    chat_logs = relationship('ChatLog')
    files = relationship('File')


class MicrotaskComment(Base):
    __tablename__ = 'microtask_comments'

    id = Column(Integer, primary_key=True, server_default=text("nextval('microtask_comments_id_seq'::regclass)"))
    user_id = Column(ForeignKey('users.id'), nullable=False)
    microtask_id = Column(ForeignKey('microtasks.id'), nullable=False)
    time_posted = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)

    microtask = relationship('Microtask')
    user = relationship('User')


class MicrotasksFile(Base):
    __tablename__ = 'microtasks_files'

    id = Column(Integer, primary_key=True, server_default=text("nextval('microtasks_files_id_seq'::regclass)"))
    microtasks_id = Column(ForeignKey('microtasks.id'), nullable=False)
    files_id = Column(ForeignKey('files.id'), nullable=False)

    files = relationship('File')
    microtasks = relationship('Microtask')


class ProjectsUsersMicrotask(Base):
    __tablename__ = 'projects_users_microtasks'

    id = Column(Integer, primary_key=True, server_default=text("nextval('projects_users_microtasks_id_seq'::regclass)"))
    projects_users_id = Column(ForeignKey('projects_users.id'), nullable=False)
    microtasks_id = Column(ForeignKey('microtasks.id'), nullable=False)

    microtasks = relationship('Microtask')
    projects_users = relationship('ProjectsUser')


class TaskCommentsFile(Base):
    __tablename__ = 'task_comments_files'

    id = Column(Integer, primary_key=True, server_default=text("nextval('task_comments_files_id_seq'::regclass)"))
    task_comments_id = Column(ForeignKey('task_comments.id'), nullable=False, server_default=text("nextval('task_comments_files_task_comments_id_seq'::regclass)"))
    files_id = Column(ForeignKey('files.id'), nullable=False, server_default=text("nextval('task_comments_files_files_id_seq'::regclass)"))

    files = relationship('File')
    task_comments = relationship('TaskComment')


class MicrotaskCommentsFile(Base):
    __tablename__ = 'microtask_comments_files'

    id = Column(Integer, primary_key=True, server_default=text("nextval('microtask_comments_files_id_seq'::regclass)"))
    microtask_comments_id = Column(ForeignKey('microtask_comments.id'), nullable=False, server_default=text("nextval('microtask_comments_files_microtask_comments_id_seq'::regclass)"))
    files_id = Column(ForeignKey('files.id'), nullable=False, server_default=text("nextval('microtask_comments_files_files_id_seq'::regclass)"))

    files = relationship('File')
    microtask_comments = relationship('MicrotaskComment')
