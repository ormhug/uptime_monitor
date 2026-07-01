"""
Подключение к базе данных PostgreSQL через SQLAlchemy.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Загружаем переменные окружения из .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не задан. Проверь файл .env (см. .env.example)")

# engine — точка входа для соединений с БД
engine = create_engine(DATABASE_URL)

# фабрика сессий: каждая сессия — это отдельная "транзакция" с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# базовый класс, от которого наследуются все ORM-модели
Base = declarative_base()


def get_db():
    """
    Зависимость FastAPI: открывает сессию БД на время обработки запроса
    и гарантированно закрывает её после, независимо от результата.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
