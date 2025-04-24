"""added enum types

Revision ID: ac6a92ad8604
Revises: e0c66fa512cf
Create Date: 2025-04-23 13:34:02.006293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ac6a92ad8604'
down_revision: Union[str, None] = 'e0c66fa512cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- Create ENUM types ---
    log_actions = postgresql.ENUM(
        'project_added', 'project_removed', 'project_added_image', 'project_removed_image',
        'project_edited_title', 'project_edited_description', 'project_added_user', 'project_removed_user',
        'project_added_label', 'project_removed_label', 'project_user_assigned_label',
        'project_user_removed_label', 'project_task_assigned_label', 'project_task_removed_label',
        'task_created', 'task_removed', 'task_edited_title', 'task_edited_description',
        'task_edited_status', 'task_edited_duedate', 'task_added_file', 'task_removed_file',
        'task_added_comment', 'task_removed_comment', 'task_comment_added_file',
        'task_comment_removed_file', 'microtask_created', 'microtask_removed',
        'microtask_edited_name', 'microtask_edited_description', 'microtask_edited_percentage',
        'microtask_edited_status', 'microtask_assigned_user', 'microtask_removed_user',
        'microtask_added_comment', 'microtask_removed_comment', 'microtask_comment_added_file',
        'microtask_comment_removed_file', 'microtask_added_file', 'microtask_removed_file',
        'microtask_added_duedate', 'microtask_removed_duedate', 'message_group_created',
        'message_group_deleted', 'message_group_edited_name', 'message_group_added_image',
        'message_group_removed_image', 'message_group_added_member', 'message_group_removed_member',
        'message_group_added_description', 'message_group_edited_description',
        'message_group_removed_description', 'login_several_failed_attempts',
        name='log_actions'
    )
    msg_state = postgresql.ENUM('sent', 'delivered', 'read', name='msg_state')
    microtask_status = postgresql.ENUM('undone', 'under_review', 'approved', name='microtask_status')
    user_roles = postgresql.ENUM('admin', 'project_manager', 'member', 'observer', name='user_roles')
    task_status = postgresql.ENUM('assigned', 'in_progress', 'under_review', 'completed', name='task_status')
    permissions = postgresql.ENUM('admin', 'user', name='permissions')

    log_actions.create(op.get_bind(), checkfirst=True)
    msg_state.create(op.get_bind(), checkfirst=True)
    microtask_status.create(op.get_bind(), checkfirst=True)
    user_roles.create(op.get_bind(), checkfirst=True)
    task_status.create(op.get_bind(), checkfirst=True)
    permissions.create(op.get_bind(), checkfirst=True)

    # --- Alter columns to use ENUMs ---
    op.alter_column('activity_log', 'action',
    existing_type=sa.TEXT(),
    type_=log_actions,
    existing_nullable=False,
    postgresql_using="action::log_actions"
    )

    op.alter_column('chat_logs', 'state',
        existing_type=sa.TEXT(),
        type_=msg_state,
        existing_nullable=False,
        postgresql_using="state::msg_state"
    )

    op.alter_column('microtasks', 'status',
        existing_type=sa.TEXT(),
        type_=microtask_status,
        existing_nullable=False,
        postgresql_using="status::microtask_status"
    )

    op.alter_column('projects_users', 'role',
        existing_type=sa.TEXT(),
        type_=user_roles,
        existing_nullable=False,
        postgresql_using="role::user_roles"
    )

    op.alter_column('tasks', 'status',
        existing_type=sa.TEXT(),
        type_=task_status,
        existing_nullable=False,
        postgresql_using="status::task_status"
    )

    op.alter_column('users', 'permission',
        existing_type=sa.TEXT(),
        type_=permissions,
        existing_nullable=False,
        postgresql_using="permission::permissions"
    )



def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column('users', 'permission',
                    existing_type=postgresql.ENUM(name='permissions'),
                    type_=sa.TEXT(),
                    existing_nullable=False)

    op.alter_column('tasks', 'status',
                    existing_type=postgresql.ENUM(name='task_status'),
                    type_=sa.TEXT(),
                    existing_nullable=False)

    op.add_column('projects_users', sa.Column('labels', sa.TEXT(), autoincrement=False, nullable=True))

    op.alter_column('projects_users', 'role',
                    existing_type=postgresql.ENUM(name='user_roles'),
                    type_=sa.TEXT(),
                    existing_nullable=False)

    op.alter_column('microtasks', 'status',
                    existing_type=postgresql.ENUM(name='microtask_status'),
                    type_=sa.TEXT(),
                    existing_nullable=False)

    op.alter_column('chat_logs', 'state',
                    existing_type=postgresql.ENUM(name='msg_state'),
                    type_=sa.TEXT(),
                    existing_nullable=False)

    op.alter_column('activity_log', 'action',
                    existing_type=postgresql.ENUM(name='log_actions'),
                    type_=sa.TEXT(),
                    existing_nullable=False)

    # --- Drop ENUMs ---
    permissions = postgresql.ENUM(name='permissions')
    task_status = postgresql.ENUM(name='task_status')
    user_roles = postgresql.ENUM(name='user_roles')
    microtask_status = postgresql.ENUM(name='microtask_status')
    msg_state = postgresql.ENUM(name='msg_state')
    log_actions = postgresql.ENUM(name='log_actions')

    permissions.drop(op.get_bind(), checkfirst=True)
    task_status.drop(op.get_bind(), checkfirst=True)
    user_roles.drop(op.get_bind(), checkfirst=True)
    microtask_status.drop(op.get_bind(), checkfirst=True)
    msg_state.drop(op.get_bind(), checkfirst=True)
    log_actions.drop(op.get_bind(), checkfirst=True)
