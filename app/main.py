"""
Точка входа FastAPI-приложения.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import monitors
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # запускаем планировщик постановки задач в очередь при старте приложения
    # (сами проверки выполняет отдельный процесс — app/worker.py)
    start_scheduler()
    yield
    # и останавливаем его при завершении работы
    stop_scheduler()


app = FastAPI(title="Uptime Monitor", lifespan=lifespan)

# добавляет стандартные HTTP-метрики (запросы, латентность, коды ответов)
# и эндпоинт /metrics для Prometheus
Instrumentator().instrument(app).expose(app)

app.include_router(monitors.router)


@app.get("/")
def root():
    """Проверка, что сервис жив."""
    return {"status": "ok"}
