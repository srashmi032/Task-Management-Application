from models.tasks import Tasks
from sqlalchemy import cast, Integer
from datetime import datetime

async def get_user_tasks(db, filters, user_id): 
    query = db.query(Tasks).filter(Tasks.user_id == user_id)

    if filters.get("status"):
        query = query.filter(Tasks.status == filters["status"])
    if filters.get("due_date"):
        query = query.filter(Tasks.due_date <= filters["due_date"])
    else:
        query = query.filter(Tasks.due_date >= datetime.utcnow())

    query = query.order_by(cast(Tasks.priority, Integer).desc()).all()

    return query

async def get_expired_tasks(db, user_id): 
    expired_tasks = db.query(Tasks).filter(Tasks.user_id == user_id, Tasks.due_date < datetime.utcnow(),
                                            Tasks.status != "completed").order_by(cast(Tasks.priority, Integer).desc())
    return expired_tasks

async def get_completed_tasks(db, user_id): 
    completed_tasks = db.query(Tasks).filter(Tasks.user_id == user_id, Tasks.status == "completed").order_by(cast(Tasks.priority, Integer).desc())
    return completed_tasks

async def get_task_by_id(db, task_id, user_id):
    task = db.query(Tasks).filter(Tasks.id == task_id, Tasks.user_id == user_id).first()
    return task