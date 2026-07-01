"""
Pydantic-схемы для валидации входящих данных и формирования ответов API.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class MonitorCreate(BaseModel):
    """Данные, которые клиент передаёт при создании монитора."""

    url: HttpUrl
    name: str
    check_interval_seconds: int = 60
    is_active: bool = True


class MonitorResponse(BaseModel):
    """Данные монитора, которые сервер возвращает клиенту."""

    id: int
    url: HttpUrl
    name: str
    check_interval_seconds: int
    is_active: bool
    created_at: datetime
    last_checked_at: datetime | None

    # позволяет создавать схему напрямую из ORM-объекта SQLAlchemy
    model_config = ConfigDict(from_attributes=True)


class CheckResultResponse(BaseModel):
    """Один результат проверки монитора."""

    id: int
    status: str
    status_code: int | None
    response_time_ms: int | None
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MonitorStatusResponse(BaseModel):
    """Текущий статус монитора и uptime за последние 24 часа."""

    monitor_id: int
    # последняя проверка; None, если проверок ещё не было
    last_result: CheckResultResponse | None
    uptime_percent_24h: float
