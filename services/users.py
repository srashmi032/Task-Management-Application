import bcrypt
from sqlalchemy.orm import Session
from database import get_db
from models.users import Users
from jwt_dependency import decode_jwt_token
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


async def get_current_user(headers=Depends(security), db: Session = Depends(get_db)):
    payload = await decode_jwt_token(headers.credentials)

    if payload.get("type") != "jwt":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("user_id")
    user = db.query(Users).filter(Users.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
