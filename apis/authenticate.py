from fastapi import Depends, Request, APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError
from database import get_db
from sqlalchemy.orm import Session
from models.users import Users
from jwt_dependency import create_jwt_token, decode_jwt_token, create_refresh_token
from services.users import hash_password, verify_password
from schemas.users import SignupRequest, LoginRequest, UserOut
from fastapi.security import HTTPBearer
from rate_limiter import limiter

security = HTTPBearer()
router = APIRouter()

@router.get("/api/v1/database-check")
@limiter.limit("20/minute")
async def database_check(request: Request, db=Depends(get_db)):
    return {"status_check": "DB connection successful"}

@router.get("/api/v1/hello")
@limiter.limit("20/minute")
async def hello(request: Request):
    return {"message": "Hello World"}

@router.get("/api/v1/refresh-access-token")
@limiter.limit("10/minute")
async def refresh_access_token(request: Request, headers=Depends(security)):
    payload = await decode_jwt_token(headers.credentials)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    token = await create_jwt_token(payload.get("user_id"))
    return {"access_token": token}

@router.post("/api/v1/users/signup", response_model=UserOut)
@limiter.limit("5/minute")
async def signup(request: Request, body: SignupRequest, db: Session = Depends(get_db)):
    user = Users(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    db.refresh(user)

    return user

@router.post("/api/v1/users/login")
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = await create_jwt_token(user.id)
    refresh_token = await create_refresh_token(user.id)

    return {"message": "Login successful", "token": access_token, "refresh_token": refresh_token}
