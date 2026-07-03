"""
Задачи, которые выполняет воркер (app/worker.py) из очереди RQ.
"""
import logging
from datetime import datetime, timezone

from app.checker import check_url
from app.database import SessionLocal
from app.models import CheckResult, Monitor

logger = logging.getLogger(__name__)


def run_check(monitor_id: int) -> None:
    """
    Проверяет один монитор и сохраняет результат в БД.

    Выполняется в процессе воркера, а не в контексте HTTP-запроса, поэтому
    сессия БД открывается вручную — Depends(get_db) здесь недоступен.
    """
    db = SessionLocal()
    try:
        monitor = db.get(Monitor, monitor_id)
        if monitor is None:
            # монитор могли удалить между постановкой задачи в очередь и её выполнением
            logger.warning("монитор %s не найден, проверка пропущена", monitor_id)
            return

        outcome = check_url(monitor.url)

        db.add(
            CheckResult(
                monitor_id=monitor.id,
                status=outcome.status,
                status_code=outcome.status_code,
                response_time_ms=outcome.response_time_ms,
            )
        )
        monitor.last_checked_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "monitor %s (%s): %s [%s], %d мс",
            monitor.id, monitor.url, outcome.status, outcome.status_code, outcome.response_time_ms,
        )
    finally:
        db.close()
