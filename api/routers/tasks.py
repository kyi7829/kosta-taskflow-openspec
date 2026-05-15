from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api import models, schemas
from api.dependencies import get_current_user, get_team_member

router = APIRouter()


def task_to_dict(task: models.Task) -> dict:
    return {
        "id": task.id,
        "team_id": task.team_id,
        "title": task.title,
        "status": task.status,
        "creator_id": task.creator_id,
        "assignee_id": task.assignee_id,
        "created_at": task.created_at.isoformat(),
    }


# ── GET /teams/{id}/tasks ─────────────────────────────────────────────────────

@router.get("/teams/{team_id}/tasks")
def list_tasks(
    team_id: int,
    filter: Optional[str] = Query(default=None),
    current_user: models.User = Depends(get_team_member),
    db: Session = Depends(get_db),
):
    query = db.query(models.Task).filter(models.Task.team_id == team_id)

    if filter == "me":
        query = query.filter(models.Task.assignee_id == current_user.id)
    elif filter == "unassigned":
        query = query.filter(models.Task.assignee_id.is_(None))

    tasks = query.order_by(models.Task.created_at.desc()).all()
    return [task_to_dict(t) for t in tasks]


# ── POST /teams/{id}/tasks ────────────────────────────────────────────────────

@router.post("/teams/{team_id}/tasks", status_code=201)
def create_task(
    team_id: int,
    body: schemas.TaskCreateRequest,
    current_user: models.User = Depends(get_team_member),
    db: Session = Depends(get_db),
):
    task = models.Task(
        team_id=team_id,
        title=body.title,
        status="TODO",
        creator_id=current_user.id,
        assignee_id=body.assignee_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task_to_dict(task)


# ── GET /tasks/{id} ───────────────────────────────────────────────────────────

@router.get("/tasks/{task_id}")
def get_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "태스크를 찾을 수 없습니다"},
        )

    # Verify user is a member of the task's team
    if current_user.team_id != task.team_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "이 팀의 멤버가 아닙니다"},
        )

    return task_to_dict(task)


# ── PUT /tasks/{id} ───────────────────────────────────────────────────────────

@router.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    body: schemas.TaskUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "태스크를 찾을 수 없습니다"},
        )

    if current_user.team_id != task.team_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "이 팀의 멤버가 아닙니다"},
        )

    if body.title is not None:
        task.title = body.title
    # Allow explicitly setting assignee_id to None
    if "assignee_id" in body.model_fields_set:
        task.assignee_id = body.assignee_id

    db.commit()
    db.refresh(task)
    return task_to_dict(task)


# ── PATCH /tasks/{id}/status ─────────────────────────────────────────────────

@router.patch("/tasks/{task_id}/status")
def update_task_status(
    task_id: int,
    body: schemas.TaskStatusRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "태스크를 찾을 수 없습니다"},
        )

    if current_user.team_id != task.team_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "이 팀의 멤버가 아닙니다"},
        )

    task.status = body.status
    db.commit()
    db.refresh(task)
    return task_to_dict(task)


# ── DELETE /tasks/{id} ───────────────────────────────────────────────────────

@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "태스크를 찾을 수 없습니다"},
        )

    if current_user.team_id != task.team_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "이 팀의 멤버가 아닙니다"},
        )

    # Check permission: creator or team owner
    team = db.query(models.Team).filter(models.Team.id == task.team_id).first()
    is_creator = task.creator_id == current_user.id
    is_owner = team and team.owner_id == current_user.id

    if not is_creator and not is_owner:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "태스크 작성자 또는 팀장만 삭제할 수 있습니다"},
        )

    db.delete(task)
    db.commit()
    return None
