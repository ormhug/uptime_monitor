"""
Точка входа FastAPI-приложения.
"""
from fastapi import FastAPI

from app.routers import monitors

app = FastAPI(title="Uptime Monitor")

app.include_router(monitors.router)


@app.get("/")
def root():
    """Проверка, что сервис жив."""
    return {"status": "ok"}
