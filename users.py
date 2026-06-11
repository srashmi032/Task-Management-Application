from sqlalchemy.orm import Session
from database import get_db
from models.users import Users
from jwt_dependency import decode_jwt_token
from fastapi import Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(headers=Depends(security), db: Session = Depends(get_db)):
    # print("headers", headers)
    userid = await decode_jwt_token(headers.credentials)
    user_id = userid['user_id'] if isinstance(userid, dict) else None
    user = db.query(Users).filter(Users.id == int(user_id)).first()
    return user