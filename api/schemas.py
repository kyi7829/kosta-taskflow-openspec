from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator, model_validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("8자 이상 입력해주세요")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    team_id: Optional[int]

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class MeResponse(BaseModel):
    id: int
    email: str
    team_id: Optional[int]

    model_config = {"from_attributes": True}


# ── Team ─────────────────────────────────────────────────────────────────────

class TeamCreateRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("팀 이름을 입력해주세요")
        if len(v) > 30:
            raise ValueError("팀 이름은 30자 이내로 입력해주세요")
        return v


class TeamJoinRequest(BaseModel):
    invite_code: str

    @field_validator("invite_code")
    @classmethod
    def validate_invite_code(cls, v: str) -> str:
        import re
        if not re.match(r"^[A-Z]{4}-[0-9]{4}$", v):
            raise ValueError("형식이 올바르지 않습니다")
        return v


class TeamOut(BaseModel):
    id: int
    name: str
    invite_code: str
    owner_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamDetailOut(BaseModel):
    id: int
    name: str
    invite_code: str
    owner_id: Optional[int]
    member_count: int

    model_config = {"from_attributes": True}


class MemberOut(BaseModel):
    id: int
    email: str
    role: str  # "owner" or "member"
    joined_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TeamJoinResponse(BaseModel):
    team: dict
    redirect: str


class TransferOwnerRequest(BaseModel):
    new_owner_id: int


# ── Task ─────────────────────────────────────────────────────────────────────

class TaskCreateRequest(BaseModel):
    title: str
    assignee_id: Optional[int] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("태스크 제목을 입력해주세요")
        if len(v) > 100:
            raise ValueError("태스크 제목은 100자 이내로 입력해주세요")
        return v


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    assignee_id: Optional[int] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("태스크 제목을 입력해주세요")
            if len(v) > 100:
                raise ValueError("태스크 제목은 100자 이내로 입력해주세요")
        return v


class TaskStatusRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("TODO", "DOING", "DONE"):
            raise ValueError("status는 TODO, DOING, DONE 중 하나여야 합니다")
        return v


class TaskOut(BaseModel):
    id: int
    team_id: int
    title: str
    status: str
    creator_id: Optional[int]
    assignee_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Message ───────────────────────────────────────────────────────────────────

class MessageCreateRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("메시지를 입력해주세요")
        if len(v) > 1000:
            raise ValueError("메시지는 1000자 이내로 입력하세요")
        return v


class MessageOut(BaseModel):
    id: int
    team_id: int
    user_id: Optional[int]
    user_email: Optional[str]
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
