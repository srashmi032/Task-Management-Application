import os
from fastapi import Depends, Request, APIRouter, HTTPException
from database import get_db
from sqlalchemy.orm import Session
from models.tasks import Tasks
from jwt_dependency import create_jwt_token
from services.users import get_current_user
from services.tasks import get_user_tasks, get_expired_tasks, get_completed_tasks, get_task_by_id
from schemas.tasks import TaskCreate, TaskUpdate
from schemas.users import UserOut
from fastapi.security import HTTPBearer
from rate_limiter import limiter

security = HTTPBearer()
router = APIRouter()

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")


def require_dev_environment():
    if ENVIRONMENT not in ("development", "local", "test"):
        raise HTTPException(status_code=404)


@router.post("/api/v1/tasks/create")
@limiter.limit("30/minute")
async def create_task(request: Request, body: TaskCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):

    task = Tasks(
        title=body.title,
        description=body.description,
        due_date=body.due_date,
        priority=body.priority,
        user_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return task

@router.post("/api/v1/tasks/update")
@limiter.limit("30/minute")
async def update_task(request: Request, task_id: int, body: TaskUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):

    task = db.query(Tasks).filter(Tasks.id == task_id, Tasks.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.due_date is not None:
        task.due_date = body.due_date
    if body.priority is not None:
        task.priority = body.priority
    if body.status is not None:
        task.status = body.status

    db.commit()
    db.refresh(task)

    return task

@router.post("/api/v1/tasks/delete")
@limiter.limit("30/minute")
async def delete_task(request: Request, task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.query(Tasks).filter(Tasks.id == task_id, Tasks.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}

@router.post("/api/v1/tasks/mark-complete")
@limiter.limit("30/minute")
async def mark_task_complete(request: Request, task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.query(Tasks).filter(Tasks.id == task_id, Tasks.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "completed"
    db.commit()
    db.refresh(task)

    return {"message": "Task marked as complete", "task": task}


# Dev-only helper for minting access tokens without a full login flow.
# Disabled unless ENVIRONMENT is development/local/test (see require_dev_environment).
@router.get("/api/v1/test/refresh-access-token")
@limiter.limit("10/minute")
async def test_mint_access_token(request: Request, user_id: int, _: None = Depends(require_dev_environment)):
    token = await create_jwt_token(user_id)
    return {"access_token": token}

@router.get("/api/v1/tasks/list")
@limiter.limit("60/minute")
async def list_tasks(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    params = dict(request.query_params)
    tasks = await get_user_tasks(db, params, user.id)
    return {"user": UserOut.model_validate(user), "tasks": tasks}

@router.get("/api/v1/tasks/expired")
@limiter.limit("60/minute")
async def expired_tasks(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    expired_tasks = await get_expired_tasks(db, user.id)
    return {"user": UserOut.model_validate(user), "expired_tasks": expired_tasks}

@router.get("/api/v1/tasks/completed")
@limiter.limit("60/minute")
async def completed_tasks(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    completed_tasks = await get_completed_tasks(db, user.id)
    return {"user": UserOut.model_validate(user), "completed_tasks": completed_tasks}

@router.get("/api/v1/tasks/{task_id}")
@limiter.limit("60/minute")
async def get_task(request: Request, task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = await get_task_by_id(db, task_id, user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"user": UserOut.model_validate(user), "task": task}
