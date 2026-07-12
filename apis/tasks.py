from fastapi import Depends, Request, APIRouter, HTTPException
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import cast, Integer
from models.users import Users
from models.tasks import Tasks
from jwt_dependency import create_jwt_token, decode_jwt_token, create_refresh_token
from services.users import get_current_user
from services.tasks import get_user_tasks, get_expired_tasks, get_completed_tasks, get_task_by_id
from fastapi.security import HTTPBearer
from rate_limiter import limiter

security = HTTPBearer()
router = APIRouter()

@router.post("/api/v1/tasks/create")
@limiter.limit("30/minute")
async def create_task(request: Request, title: str, description: str, due_date: str, priority: str, db: Session = Depends(get_db), user=Depends(get_current_user)):

    task = Tasks(title=title, description=description, due_date=due_date, priority=priority, user_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)

    return task

@router.post("/api/v1/tasks/update")
@limiter.limit("30/minute")
async def update_task(request: Request, task_id: int, title: str = None, description: str = None, due_date: str = None, priority: str = None, status: str = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
   
    task = db.query(Tasks).filter(Tasks.id == task_id and Tasks.user_id == user.id).first()
    if not task:
        return {"error": "Task not found"}

    if title:
        task.title = title
    if description:
        task.description = description
    if due_date:
        task.due_date = due_date
    if priority:
        task.priority = priority
   

    db.commit()
    db.refresh(task)

    return task

@router.post("/api/v1/tasks/delete")
@limiter.limit("30/minute")
async def delete_task(request: Request, task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from models.tasks import Tasks
    task = db.query(Tasks).filter(Tasks.id == task_id and Tasks.user_id == user.id).first()
    if not task:
        return {"error": "Task not found"}

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}

@router.post("/api/v1/tasks/mark-complete")
@limiter.limit("30/minute")
async def mark_task_complete(request: Request, task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from models.tasks import Tasks
    task = db.query(Tasks).filter(Tasks.id == task_id and Tasks.user_id == user.id).first()
    if not task:
        return {"error": "Task not found"}

    task.status = "completed"
    db.commit()
    db.refresh(task)

    return {"message": "Task marked as complete", "task": task}


# TODO: Remove this endpoint in production, this is just for testing purposes

@router.get("/api/v1/test/refresh-access-token")
@limiter.limit("10/minute")
async def refresh_access_token(request: Request, user_id: int):
    try:
        token = await create_jwt_token({"user_id": user_id})
        return {"access_token": token}
    
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/v1/tasks/list")
@limiter.limit("60/minute")
async def list_tasks(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    params = dict(request.query_params)
    tasks = await get_user_tasks(db, params, user.id)
    return {"user": user, "tasks": tasks}

@router.get("/api/v1/tasks/expired")
@limiter.limit("60/minute")
async def expired_tasks(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    expired_tasks = await get_expired_tasks(db, user.id)
    return {"user": user, "expired_tasks": expired_tasks}

@router.get("/api/v1/tasks/completed")
@limiter.limit("60/minute")
async def completed_tasks(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    completed_tasks = await get_completed_tasks(db, user.id)
    return {"user": user, "completed_tasks": completed_tasks}

@router.get("/api/v1/tasks/{task_id}")
@limiter.limit("60/minute")
async def get_task(request: Request, task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = await get_task_by_id(db, task_id, user.id)
    if not task:
        return {"error": "Task not found"}
    return {"user": user, "task": task}