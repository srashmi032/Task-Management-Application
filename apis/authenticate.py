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

# app = FastAPI()
security = HTTPBearer()
router = APIRouter()

@router.get("/api/v1/database-check")
async def root(db=Depends(get_db)):
    return {"status_check": "DB connection successful"}

@router.get("/api/v1/hello")
async def root():
    return {"message": "Hello World"}

@router.get("/api/v1/refresh-access-token")
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
    
@router.post("/api/v1/users/signup")
async def signup(username: str, email: str, password: str, first_name: str, last_name: str=None,
                db: Session = Depends(get_db)):
    
    user = Users(first_name=first_name, email=email, last_name=last_name, password_hash=password, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
    
@router.post("/api/v1/users/login")
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