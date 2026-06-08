from fastapi import Depends, FastAPI
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import cast, Integer
from models.users import Users
from models.tasks import Tasks

app = FastAPI()


@app.get("/api/v1/database-check")
async def root(db=Depends(get_db)):
    return {"status_check": "DB connection successful"}

@app.get("/api/v1/hello")
async def root():
    return {"message": "Hello World"}

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
    if not user or user.password_hash != password:
        return {"error": "Invalid username or password"}

    return {"message": "Login successful"}


@app.post("/api/v1/tasks/create")
async def create_task(title: str, description: str, due_date: str, priority: str, user_id: int, db: Session = Depends(get_db)):
    
    task = Tasks(title=title, description=description, due_date=due_date, priority=priority, user_id=user_id)
    db.add(task)
    db.commit()
    db.refresh(task)

    return task

@app.post("/api/v1/tasks/update")
async def update_task(task_id: int, title: str = None, description: str = None, due_date: str = None, priority: str = None, status: str = None, db: Session = Depends(get_db)):
   
    task = db.query(Tasks).filter(Tasks.id == task_id).first()
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
    if status:
        task.status = status

    db.commit()
    db.refresh(task)

    return task

@app.post("/api/v1/tasks/delete")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    from models.tasks import Tasks
    task = db.query(Tasks).filter(Tasks.id == task_id).first()
    if not task:
        return {"error": "Task not found"}

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}

@app.post("/api/v1/tasks/mark-complete")
async def mark_task_complete(task_id: int, db: Session = Depends(get_db)):
    from models.tasks import Tasks
    task = db.query(Tasks).filter(Tasks.id == task_id).first()
    if not task:
        return {"error": "Task not found"}

    task.status = "completed"
    db.commit()
    db.refresh(task)

    return {"message": "Task marked as complete", "task": task}

@app.get("/api/v1/tasks/list")
async def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Tasks).order_by(cast(Tasks.priority, Integer).desc()).all()
    return tasks