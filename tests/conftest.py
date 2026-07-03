"""
Общие фикстуры для тестов.

Тестовая БД — SQLite in-memory, а не Postgres. Модели (Monitor, CheckResult)
используют только переносимые типы SQLAlchemy (Integer, String, Boolean,
DateTime, ForeignKey) без Postgres-специфики (JSONB, ARRAY и т.п.), поэтому
SQLite отлично подходит: тесты не требуют поднятой Postgres и не трогают
рабочую/прод базу.
"""
import os

# ставим до импорта app.database — на случай если .env отсутствует (например, в CI),
# чтобы модуль не падал с RuntimeError при импорте
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

# StaticPool держит одно и то же соединение на всё время жизни engine —
# без этого каждое новое соединение получало бы свою пустую in-memory базу
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    """Подменяет боевую сессию БД на сессию тестовой SQLite-базы."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    """Перед каждым тестом создаёт пустые таблицы, после теста — удаляет их."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture
async def client():
    """Асинхронный HTTP-клиент, обращающийся к FastAPI-приложению напрямую (без сети)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
