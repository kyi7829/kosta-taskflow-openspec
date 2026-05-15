import random
import string
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from api.database import get_db
from api import models, schemas
from api.dependencies import get_current_user, get_team_member

router = APIRouter()


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def generate_invite_code(db: Session) -> str:
    """Generate a unique invite code in XXXX-9999 format."""
    while True:
        letters = "".join(random.choices(string.ascii_uppercase, k=4))
        digits = "".join(random.choices(string.digits, k=4))
        code = f"{letters}-{digits}"
        exists = db.query(models.Team).filter(models.Team.invite_code == code).first()
        if not exists:
            return code


# ── POST /teams ───────────────────────────────────────────────────────────────

@router.post("", status_code=201)
def create_team(
    body: schemas.TeamCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.team_id is not None:
        raise HTTPException(
            status_code=409,
            detail={"code": "ALREADY_IN_TEAM", "message": "이미 팀에 소속되어 있습니다"},
        )

    invite_code = generate_invite_code(db)

    team = models.Team(
        name=body.name,
        invite_code=invite_code,
        owner_id=None,  # will be set after user update
    )
    db.add(team)
    db.flush()  # get team.id without committing

    # Set owner and update user's team membership
    team.owner_id = current_user.id
    current_user.team_id = team.id
    current_user.team_joined_at = utcnow()

    db.commit()
    db.refresh(team)

    return {
        "id": team.id,
        "name": team.name,
        "invite_code": team.invite_code,
        "owner_id": team.owner_id,
        "created_at": team.created_at.isoformat(),
    }


# ── POST /teams/join ──────────────────────────────────────────────────────────

@router.post("/join")
def join_team(
    body: schemas.TeamJoinRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.team_id is not None:
        raise HTTPException(
            status_code=409,
            detail={"code": "ALREADY_IN_TEAM", "message": "이미 다른 팀에 소속되어 있습니다"},
        )

    team = db.query(models.Team).filter(models.Team.invite_code == body.invite_code).first()
    if not team:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "해당 초대코드를 찾을 수 없습니다"},
        )

    current_user.team_id = team.id
    current_user.team_joined_at = utcnow()
    db.commit()

    member_count = db.query(models.User).filter(models.User.team_id == team.id).count()

    return {
        "team": {"id": team.id, "name": team.name, "member_count": member_count},
        "redirect": f"/teams/{team.id}",
    }


# ── GET /teams/{id} ───────────────────────────────────────────────────────────

@router.get("/{team_id}")
def get_team(
    team_id: int,
    current_user: models.User = Depends(get_team_member),
    db: Session = Depends(get_db),
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "팀을 찾을 수 없습니다"},
        )

    member_count = db.query(models.User).filter(models.User.team_id == team_id).count()

    return {
        "id": team.id,
        "name": team.name,
        "invite_code": team.invite_code,
        "owner_id": team.owner_id,
        "member_count": member_count,
    }


# ── GET /teams/{id}/members ───────────────────────────────────────────────────

@router.get("/{team_id}/members")
def get_members(
    team_id: int,
    current_user: models.User = Depends(get_team_member),
    db: Session = Depends(get_db),
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "팀을 찾을 수 없습니다"},
        )

    members = db.query(models.User).filter(models.User.team_id == team_id).all()

    result = []
    for m in members:
        result.append({
            "id": m.id,
            "email": m.email,
            "role": "owner" if m.id == team.owner_id else "member",
            "joined_at": m.team_joined_at.isoformat() if m.team_joined_at else None,
        })
    return result


# ── DELETE /teams/{id}/leave ─────────────────────────────────────────────────

@router.delete("/{team_id}/leave", status_code=204)
def leave_team(
    team_id: int,
    current_user: models.User = Depends(get_team_member),
    db: Session = Depends(get_db),
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "팀을 찾을 수 없습니다"},
        )

    if team.owner_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "OWNER_MUST_TRANSFER",
                "message": "팀장은 위임 또는 팀 삭제 후 탈퇴할 수 있습니다",
            },
        )

    # 탈퇴하는 유저가 담당한 태스크의 assignee_id를 NULL로 정리
    db.query(models.Task).filter(
        models.Task.team_id == team_id,
        models.Task.assignee_id == current_user.id,
    ).update({"assignee_id": None})

    current_user.team_id = None
    current_user.team_joined_at = None
    db.commit()
    return None


# ── PATCH /teams/{id}/transfer-owner ─────────────────────────────────────────

@router.patch("/{team_id}/transfer-owner")
def transfer_owner(
    team_id: int,
    body: schemas.TransferOwnerRequest,
    current_user: models.User = Depends(get_team_member),
    db: Session = Depends(get_db),
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "팀을 찾을 수 없습니다"},
        )

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "팀장만 소유권을 이전할 수 있습니다"},
        )

    # Verify new owner is in the same team
    new_owner = db.query(models.User).filter(models.User.id == body.new_owner_id).first()
    if not new_owner or new_owner.team_id != team_id:
        raise HTTPException(
            status_code=400,
            detail={"code": "NOT_TEAM_MEMBER", "message": "해당 사용자는 이 팀의 멤버가 아닙니다"},
        )

    team.owner_id = body.new_owner_id
    db.commit()
    db.refresh(team)

    return {
        "id": team.id,
        "name": team.name,
        "owner_id": team.owner_id,
    }


# ── DELETE /teams/{id} ────────────────────────────────────────────────────────

@router.delete("/{team_id}", status_code=204)
def delete_team(
    team_id: int,
    current_user: models.User = Depends(get_team_member),
    db: Session = Depends(get_db),
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "팀을 찾을 수 없습니다"},
        )

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "팀장만 팀을 삭제할 수 있습니다"},
        )

    # Set all members' team_id to NULL
    db.query(models.User).filter(models.User.team_id == team_id).update(
        {"team_id": None, "team_joined_at": None}
    )

    # Delete team (tasks and messages cascade)
    db.delete(team)
    db.commit()
    return None
