"""
Кастомные бизнес-метрики Prometheus.

Отдельно от них prometheus-fastapi-instrumentator (подключён в main.py) сам
экспортирует стандартные HTTP-метрики API (запросы, латентность, коды ответов).
"""
from prometheus_client import Counter, Gauge, Histogram

# сколько всего проверок мониторов выполнено, с разбивкой по исходу (up/down)
monitor_checks_total = Counter(
    "monitor_checks_total",
    "Общее количество проверок мониторов",
    ["status"],
)

# сколько времени занимает одна проверка монитора (check_url), в секундах
monitor_check_duration_seconds = Histogram(
    "monitor_check_duration_seconds",
    "Длительность одной проверки монитора",
)

# сколько сейчас активных (is_active=True) мониторов
active_monitors_total = Gauge(
    "active_monitors_total",
    "Текущее количество активных мониторов",
)
