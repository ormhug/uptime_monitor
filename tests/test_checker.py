"""
Тесты для checker.check_url — httpx замокан, реальные сетевые запросы не делаются.
"""
from unittest.mock import MagicMock, patch

import httpx

from app.checker import check_url


def _mock_response(status_code: int) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    return response


@patch("app.checker.httpx.get")
def test_check_url_success(mock_get):
    """Код ответа 200 — монитор считается доступным."""
    mock_get.return_value = _mock_response(200)

    outcome = check_url("https://example.com")

    assert outcome.status == "up"
    assert outcome.status_code == 200
    assert outcome.response_time_ms >= 0


@patch("app.checker.httpx.get")
def test_check_url_down(mock_get):
    """Код ответа вне диапазона 2xx — монитор считается недоступным."""
    mock_get.return_value = _mock_response(500)

    outcome = check_url("https://example.com")

    assert outcome.status == "down"
    assert outcome.status_code == 500


@patch("app.checker.httpx.get")
def test_check_url_timeout(mock_get):
    """Таймаут — тоже "down", а не необработанное исключение наружу."""
    mock_get.side_effect = httpx.TimeoutException("timed out")

    outcome = check_url("https://example.com")

    assert outcome.status == "down"
    assert outcome.status_code is None
