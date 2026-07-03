"""
Планировщик: раз в N секунд ставит задачи проверки активных мониторов в очередь RQ.

Сам планировщик по-прежнему работает внутри процесса API (через APScheduler),
но больше не выполняет проверки сам — он только кладёт задачи в очередь Redis.
Выполняет их отдельный процесс-воркер (app/worker.py).
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from rq import Queue

from app.database import SessionLocal
from app.models import Monitor
from app.redis_conn import redis_conn
from app.tasks import run_check

logger = logging.getLogger(__name__)

# как часто планировщик ставит в очередь проверки активных мониторов, в секундах
SCHEDULER_INTERVAL_SECONDS = 30

scheduler = BackgroundScheduler()
queue = Queue("checks", connection=redis_conn)


def enqueue_checks() -> None:
    """Ставит в очередь задачу проверки для каждого активного монитора."""
    db = SessionLocal()
    try:
        monitors = db.query(Monitor).filter(Monitor.is_active.is_(True)).all()
    finally:
        db.close()

    for monitor in monitors:
        queue.enqueue(run_check, monitor.id)
        logger.info("монитор %s поставлен в очередь на проверку", monitor.id)


def start_scheduler() -> None:
    """Запускает планировщик (вызывается при старте приложения)."""
    scheduler.add_job(enqueue_checks, "interval", seconds=SCHEDULER_INTERVAL_SECONDS, id="enqueue_checks")
    scheduler.start()


def stop_scheduler() -> None:
    """Останавливает планировщик (вызывается при остановке приложения)."""
    scheduler.shutdown(wait=False)
