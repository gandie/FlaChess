from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.web import STATIC_DIR, router as web_router

app = FastAPI(title="Fla Chess")
app.include_router(api_router, prefix="/api")
app.include_router(web_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
