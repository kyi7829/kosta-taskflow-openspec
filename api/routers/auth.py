from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api import models, schemas
from api.auth import hash_password, verify_password, create_access_token
from api.dependencies import get_current_user

router = APIRouter()


@router.post("/signup", status_code=201)
def signup(body: schemas.SignupRequest, db: Session = Depends(get_db)):
    # Check duplicate email
    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"code": "EMAIL_TAKEN", "message": "이미 가입된 이메일입니다"},
        )

    user = models.User(
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "team_id": user.team_id},
    }


@router.post("/login")
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "이메일 또는 비밀번호가 일치하지 않습니다",
            },
        )

    token = create_access_token(user.id)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "team_id": user.team_id},
    }


@router.post("/logout")
def logout(current_user: models.User = Depends(get_current_user)):
    # Stateless — client deletes localStorage token
    return {}


@router.get("/me")
def me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "team_id": current_user.team_id,
    }
