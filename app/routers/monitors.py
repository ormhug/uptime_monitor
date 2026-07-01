"""
Эндпоинты для работы с мониторами.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Monitor
from app.schemas import MonitorCreate, MonitorResponse

router = APIRouter(prefix="/monitors", tags=["monitors"])


@router.post("", response_model=MonitorResponse)
def create_monitor(monitor: MonitorCreate, db: Session = Depends(get_db)):
    """Создать новый монитор."""
    db_monitor = Monitor(
        url=str(monitor.url),
        name=monitor.name,
        check_interval_seconds=monitor.check_interval_seconds,
        is_active=monitor.is_active,
    )
    db.add(db_monitor)
    db.commit()
    db.refresh(db_monitor)
    return db_monitor


@router.get("", response_model=List[MonitorResponse])
def list_monitors(db: Session = Depends(get_db)):
    """Получить список всех мониторов."""
    return db.query(Monitor).all()
