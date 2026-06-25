from fastapi import FastAPI
from apis import auth_router, tasks_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(tasks_router)

