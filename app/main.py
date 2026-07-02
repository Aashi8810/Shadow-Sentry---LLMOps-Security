from fastapi import FastAPI
from app.config import settings
from app.db.database import engine, Base
from app.routes import chat, admin

# Auto-build our DB structure layout on boot execution
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(chat.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"status": "online", "service": settings.app_name}