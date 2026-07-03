"""
Эндпоинты для работы с мониторами.
"""
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CheckResult, Monitor
from app.schemas import CheckResultResponse, MonitorCreate, MonitorResponse, MonitorStatusResponse

router = APIRouter(prefix="/monitors", tags=["monitors"])

# за сколько последних часов считаем uptime %
UPTIME_WINDOW_HOURS = 24
# сколько последних проверок отдаём в истории
HISTORY_LIMIT = 20


def _get_monitor_or_404(monitor_id: int, db: Session) -> Monitor:
    """Достаёт монитор по id или бросает 404, если такого нет."""
    monitor = db.get(Monitor, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=404, detail="Монитор не найден")
    return monitor


@router.post("", response_model=MonitorResponse, status_code=201)
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


@router.get("/{monitor_id}/history", response_model=List[CheckResultResponse])
def get_monitor_history(monitor_id: int, db: Session = Depends(get_db)):
    """Последние проверки монитора, от новых к старым."""
    _get_monitor_or_404(monitor_id, db)

    return (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )


@router.get("/{monitor_id}/status", response_model=MonitorStatusResponse)
def get_monitor_status(monitor_id: int, db: Session = Depends(get_db)):
    """Текущий статус монитора (последняя проверка) и uptime % за последние 24 часа."""
    _get_monitor_or_404(monitor_id, db)

    last_result = (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc())
        .first()
    )

    window_start = datetime.now(timezone.utc) - timedelta(hours=UPTIME_WINDOW_HOURS)
    recent_results = db.query(CheckResult.status).filter(
        CheckResult.monitor_id == monitor_id, CheckResult.checked_at >= window_start
    )
    total = recent_results.count()
    up_count = recent_results.filter(CheckResult.status == "up").count()

    uptime_percent = (up_count / total * 100) if total else 0.0

    return MonitorStatusResponse(
        monitor_id=monitor_id,
        last_result=last_result,
        uptime_percent_24h=round(uptime_percent, 2),
    )
