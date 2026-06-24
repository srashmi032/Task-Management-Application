from fastapi import Depends, Request, FastAPI, HTTPException
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import cast, Integer
from models.users import Users
from models.tasks import Tasks
from jwt_dependency import create_jwt_token, decode_jwt_token, create_refresh_token
from services.users import get_current_user
from services.tasks import get_user_tasks, get_expired_tasks, get_completed_tasks, get_task_by_id
from fastapi.security import HTTPBearer

app = FastAPI()

security = HTTPBearer()


@app.get("/api/v1/database-check")
async def root(db=Depends(get_db)):
    return {"status_check": "DB connection successful"}

@app.get("/api/v1/hello")
async def root():
    return {"message": "Hello World"}

@app.get("/api/v1/refresh-access-token")
async def refresh_access_token(headers=Depends(security)):
    try:
        payload = await decode_jwt_token(headers.credentials)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )
        user_id = payload.get("user_id") if isinstance(payload, dict) else None
        user_id = user_id['user_id'] if isinstance(user_id, dict) else None
        
        token = await create_jwt_token({"user_id": user_id})
        return {"access_token": token}
    
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/api/v1/users/signup")
async def signup(username: str, email: str, password: str, first_name: str, last_name: str=None,
                db: Session = Depends(get_db)):
    
    user = Users(first_name=first_name, email=email, last_name=last_name, password_hash=password, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
    
@app.post("/api/v1/users/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.username == username).first()
    print("userd", user.id)
    if not user or user.password_hash != password:
        return {"error": "Invalid username or password"}
    print(user.id)
    access_token = await create_jwt_token(
        {"user_id": user.id}
    )
    print("token", access_token)
    refresh_access_token = await create_refresh_token(
        {"user_id": user.id}
    )

    return {"message": "Login successful", "token": access_token, "refresh_token": refresh_access_token}


@app.post("/api/v1/tasks/create")
async def create_task(title: str, description: str, due_date: str, priority: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    
    task = Tasks(title=title, description=description, due_date=due_date, priority=priority, user_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)

    return task

@app.post("/api/v1/tasks/update")
async def update_task(task_id: int, title: str = None, description: str = None, due_date: str = None, priority: str = None, status: str = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
   
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

@app.post("/api/v1/tasks/delete")
async def delete_task(task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from models.tasks import Tasks
    task = db.query(Tasks).filter(Tasks.id == task_id and Tasks.user_id == user.id).first()
    if not task:
        return {"error": "Task not found"}

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}

@app.post("/api/v1/tasks/mark-complete")
async def mark_task_complete(task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from models.tasks import Tasks
    task = db.query(Tasks).filter(Tasks.id == task_id and Tasks.user_id == user.id).first()
    if not task:
        return {"error": "Task not found"}

    task.status = "completed"
    db.commit()
    db.refresh(task)

    return {"message": "Task marked as complete", "task": task}


# TODO: Remove this endpoint in production, this is just for testing purposes

@app.get("/api/v1/test/refresh-access-token")
async def refresh_access_token(user_id: int):
    try:
        token = await create_jwt_token({"user_id": user_id})
        return {"access_token": token}
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/tasks/list")     
async def list_tasks(request:Request,  db: Session = Depends(get_db), user=Depends(get_current_user)):
    params = dict(request.query_params)
    tasks = await get_user_tasks(db, params, user.id)
    return {"user": user, "tasks": tasks}

@app.get("/api/v1/tasks/expired")
async def expired_tasks(db: Session = Depends(get_db), user=Depends(get_current_user)):
    expired_tasks = await get_expired_tasks(db, user.id)
    return {"user": user, "expired_tasks": expired_tasks}

@app.get("/api/v1/tasks/completed")
async def completed_tasks(db: Session = Depends(get_db), user=Depends(get_current_user)):
    completed_tasks = await get_completed_tasks(db, user.id)
    return {"user": user, "completed_tasks": completed_tasks}

@app.get("/api/v1/tasks/{task_id}")
async def get_task(task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = await get_task_by_id(db, task_id, user.id)
    if not task:
        return {"error": "Task not found"}
    return {"user": user, "task": task}