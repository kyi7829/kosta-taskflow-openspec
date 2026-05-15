from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from api.database import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    team_joined_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    team = relationship("Team", foreign_keys=[team_id], back_populates="members")
    owned_team = relationship("Team", foreign_keys="Team.owner_id", back_populates="owner")
    created_tasks = relationship("Task", foreign_keys="Task.creator_id", back_populates="creator")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    messages = relationship("Message", back_populates="user")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), nullable=False)
    invite_code = Column(String(9), unique=True, nullable=False)
    # use_alter=True to handle circular FK (users.team_id <-> teams.owner_id)
    owner_id = Column(
        Integer,
        ForeignKey("users.id", use_alter=True, name="fk_teams_owner_id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_team")
    members = relationship("User", foreign_keys="User.team_id", back_populates="team")
    tasks = relationship("Task", back_populates="team", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="team", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(100), nullable=False)
    status = Column(String(10), nullable=False, default="TODO")  # TODO/DOING/DONE
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    team = relationship("Team", back_populates="tasks")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    team = relationship("Team", back_populates="messages")
    user = relationship("User", back_populates="messages")


# Indexes (Task 2.5)
Index("ix_tasks_team_id_created_at", Task.team_id, Task.created_at)
Index("ix_messages_team_id_created_at", Message.team_id, Message.created_at)
Index("ix_teams_invite_code", Team.invite_code)
Index("ix_users_team_id", User.team_id)
