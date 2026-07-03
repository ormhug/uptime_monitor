"""
Тесты для tasks.run_check — сессия БД подменяется на тестовую (SQLite in-memory
из conftest.py), check_url замокан по аналогии с test_checker.py.
"""
from unittest.mock import patch

from app.checker import CheckOutcome
from app.models import CheckResult, Monitor
from app.tasks import run_check
from tests.conftest import TestingSessionLocal


def _create_monitor() -> int:
    db = TestingSessionLocal()
    try:
        monitor = Monitor(url="https://example.com", name="Example")
        db.add(monitor)
        db.commit()
        db.refresh(monitor)
        return monitor.id
    finally:
        db.close()


@patch("app.tasks.SessionLocal", TestingSessionLocal)
@patch("app.tasks.check_url")
def test_run_check_saves_result_and_updates_monitor(mock_check_url):
    """Проверка сохраняет CheckResult и обновляет last_checked_at монитора."""
    mock_check_url.return_value = CheckOutcome(status="up", status_code=200, response_time_ms=123)
    monitor_id = _create_monitor()

    run_check(monitor_id)

    db = TestingSessionLocal()
    try:
        monitor = db.get(Monitor, monitor_id)
        assert monitor.last_checked_at is not None

        results = db.query(CheckResult).filter(CheckResult.monitor_id == monitor_id).all()
        assert len(results) == 1
        assert results[0].status == "up"
        assert results[0].status_code == 200
        assert results[0].response_time_ms == 123
    finally:
        db.close()


@patch("app.tasks.SessionLocal", TestingSessionLocal)
@patch("app.tasks.check_url")
def test_run_check_missing_monitor_does_not_crash(mock_check_url):
    """Монитор мог быть удалён между постановкой задачи и её выполнением — просто пропускаем."""
    run_check(999)

    mock_check_url.assert_not_called()
