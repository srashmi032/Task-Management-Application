from jose import jwt
from env import SECRET_KEY
from datetime import datetime, timedelta

async def create_jwt_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

async def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        return "Acess token has expired"
    except jwt.InvalidTokenError:
        return "Invalid access token"
    

