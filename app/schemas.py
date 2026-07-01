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

    # позволяет создавать схему напрямую из ORM-объекта SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
