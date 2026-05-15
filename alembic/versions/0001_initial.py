"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Create users table WITHOUT team_id FK yet (circular FK resolution)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("team_joined_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Step 2: Create teams table with owner_id referencing users
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(30), nullable=False),
        sa.Column("invite_code", sa.String(9), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("invite_code", name="uq_teams_invite_code"),
    )
    op.create_index("ix_teams_invite_code", "teams", ["invite_code"])

    # Step 3: Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="TODO"),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assignee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tasks_team_id_created_at", "tasks", ["team_id", "created_at"])

    # Step 4: Create messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_messages_team_id_created_at", "messages", ["team_id", "created_at"])

    # Step 5: ALTER TABLE to add FKs for circular references
    # teams.owner_id -> users.id (use_alter)
    with op.batch_alter_table("teams", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_teams_owner_id", "users", ["owner_id"], ["id"], ondelete="SET NULL"
        )

    # users.team_id -> teams.id
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_users_team_id", "teams", ["team_id"], ["id"], ondelete="SET NULL"
        )
    op.create_index("ix_users_team_id", "users", ["team_id"])


def downgrade() -> None:
    # Drop FK constraints first
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("fk_users_team_id", type_="foreignkey")
        batch_op.drop_index("ix_users_team_id")

    with op.batch_alter_table("teams", schema=None) as batch_op:
        batch_op.drop_constraint("fk_teams_owner_id", type_="foreignkey")

    op.drop_table("messages")
    op.drop_table("tasks")
    op.drop_table("teams")
    op.drop_table("users")
