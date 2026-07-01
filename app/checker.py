"""
Логика одной проверки доступности сайта.
"""
import time
from dataclasses import dataclass

import httpx

# таймаут ожидания ответа от сайта, в секундах
CHECK_TIMEOUT_SECONDS = 10.0


@dataclass
class CheckOutcome:
    """Результат проверки одного URL."""

    status: str  # "up" или "down"
    status_code: int | None
    response_time_ms: int


def check_url(url: str) -> CheckOutcome:
    """
    Делает GET-запрос по указанному URL и определяет, доступен ли сайт.

    Сайт считается доступным ("up"), если код ответа 2xx.
    Любая ошибка (таймаут, недоступность, редирект в никуда и т.д.) — "down".
    """
    started_at = time.monotonic()
    try:
        response = httpx.get(url, timeout=CHECK_TIMEOUT_SECONDS, follow_redirects=True)
        response_time_ms = int((time.monotonic() - started_at) * 1000)

        if 200 <= response.status_code < 300:
            return CheckOutcome(status="up", status_code=response.status_code, response_time_ms=response_time_ms)
        return CheckOutcome(status="down", status_code=response.status_code, response_time_ms=response_time_ms)

    except httpx.HTTPError:
        response_time_ms = int((time.monotonic() - started_at) * 1000)
        return CheckOutcome(status="down", status_code=None, response_time_ms=response_time_ms)
