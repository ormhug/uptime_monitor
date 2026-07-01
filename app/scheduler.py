"""
Фоновый планировщик: раз в N секунд проверяет все активные мониторы.

На этом этапе (Этап 1 roadmap) работает в рамках того же процесса FastAPI,
без отдельного воркера и очереди — это добавится на Этапе 2.
"""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.checker import check_url
from app.database import SessionLocal
from app.models import CheckResult, Monitor

logger = logging.getLogger(__name__)

# как часто планировщик запускает проверку всех активных мониторов, в секундах
SCHEDULER_INTERVAL_SECONDS = 30

scheduler = BackgroundScheduler()


def run_checks() -> None:
    """Проверяет все активные мониторы и сохраняет результаты в БД."""
    db = SessionLocal()
    try:
        monitors = db.query(Monitor).filter(Monitor.is_active.is_(True)).all()
        for monitor in monitors:
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

            logger.info(
                "monitor %s (%s): %s [%s], %d мс",
                monitor.id, monitor.url, outcome.status, outcome.status_code, outcome.response_time_ms,
            )

        db.commit()
    finally:
        db.close()


def start_scheduler() -> None:
    """Запускает планировщик (вызывается при старте приложения)."""
    scheduler.add_job(run_checks, "interval", seconds=SCHEDULER_INTERVAL_SECONDS, id="check_monitors")
    scheduler.start()


def stop_scheduler() -> None:
    """Останавливает планировщик (вызывается при остановке приложения)."""
    scheduler.shutdown(wait=False)
