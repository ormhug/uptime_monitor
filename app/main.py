"""
Точка входа FastAPI-приложения.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import monitors
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # запускаем фоновый планировщик проверок при старте приложения
    start_scheduler()
    yield
    # и останавливаем его при завершении работы
    stop_scheduler()


app = FastAPI(title="Uptime Monitor", lifespan=lifespan)

app.include_router(monitors.router)


@app.get("/")
def root():
    """Проверка, что сервис жив."""
    return {"status": "ok"}
