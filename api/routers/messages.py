from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api import models, schemas
from api.dependencies import get_current_user, get_team_member

router = APIRouter()


def message_to_dict(msg: models.Message) -> dict:
    return {
        "id": msg.id,
        "team_id": msg.team_id,
        "user_id": msg.user_id,
        "user_email": msg.user.email if msg.user else None,
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
    }


# ── GET /teams/{id}/messages ──────────────────────────────────────────────────

@router.get("/teams/{team_id}/messages")
def list_messages(
    team_id: int,
    since: Optional[str] = Query(default=None),
    current_user: models.User = Depends(get_team_member),
    db: Session = Depends(get_db),
):
    query = db.query(models.Message).filter(models.Message.team_id == team_id)

    if since:
        try:
            # Parse ISO8601 datetime
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            # Remove timezone info for naive comparison
            if since_dt.tzinfo:
                since_dt = since_dt.replace(tzinfo=None)
            query = query.filter(models.Message.created_at > since_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"code": "VALIDATION_ERROR", "message": "since 파라미터 형식이 올바르지 않습니다"},
            )
        messages = query.order_by(models.Message.created_at.asc()).all()
    else:
        # Latest 50, return in ascending order
        messages = (
            query.order_by(models.Message.created_at.desc())
            .limit(50)
            .all()
        )
        messages = list(reversed(messages))

    return [message_to_dict(m) for m in messages]


# ── POST /teams/{id}/messages ─────────────────────────────────────────────────

@router.post("/teams/{team_id}/messages", status_code=201)
def create_message(
    team_id: int,
    body: schemas.MessageCreateRequest,
    current_user: models.User = Depends(get_team_member),
    db: Session = Depends(get_db),
):
    if len(body.content) > 1000:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TOO_LONG",
                "message": "메시지는 1000자 이내로 입력하세요",
                "limit": 1000,
                "actual": len(body.content),
            },
        )

    msg = models.Message(
        team_id=team_id,
        user_id=current_user.id,
        content=body.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {
        "id": msg.id,
        "team_id": msg.team_id,
        "user_id": msg.user_id,
        "user_email": current_user.email,
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
    }


# ── DELETE /messages/{id} ─────────────────────────────────────────────────────

@router.delete("/messages/{message_id}", status_code=204)
def delete_message(
    message_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msg = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not msg:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "메시지를 찾을 수 없습니다"},
        )

    if msg.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_OWNER", "message": "본인의 메시지만 삭제할 수 있습니다"},
        )

    db.delete(msg)
    db.commit()
    return None
