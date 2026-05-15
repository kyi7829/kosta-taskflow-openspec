from fastapi import Depends, HTTPException, Header, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from jose import JWTError, ExpiredSignatureError
from typing import Optional

from api.database import get_db
from api import models
from api.auth import decode_token


def error_response(code: str, message: str, status_code: int):
    from fastapi import HTTPException
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "로그인이 필요합니다"},
        )
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"code": "TOKEN_EXPIRED", "message": "인증이 만료되었습니다"},
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "유효하지 않은 인증 토큰입니다"},
        )

    user_id = int(payload.get("sub", 0))
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "사용자를 찾을 수 없습니다"},
        )
    return user


def get_team_member(
    team_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.User:
    """Verify user is a member of the given team."""
    if current_user.team_id != team_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "이 팀의 멤버가 아닙니다"},
        )
    return current_user
