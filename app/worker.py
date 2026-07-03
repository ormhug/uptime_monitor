"""
Точка входа RQ-воркера — отдельный процесс, слушающий очередь Redis и
выполняющий задачи проверки мониторов (app/tasks.py::run_check).

Запуск (из корня проекта, при активном .venv):
    python -m app.worker

Используется SimpleWorker, а не стандартный rq.Worker: обычный Worker форкает
дочерний процесс (os.fork) на каждую задачу, а на Windows fork недоступен.
SimpleWorker выполняет задачи в своём же процессе — этого достаточно для
дев-окружения на этом этапе (без изоляции падений между задачами).

Метрики monitor_checks_total/monitor_check_duration_seconds (app/metrics.py)
инкрементируются внутри run_check, то есть в этом самом процессе. prometheus_client
хранит метрики в памяти процесса — они НЕ появятся на /metrics API, у воркера
должен быть свой собственный HTTP-эндпоинт с метриками, поэтому здесь поднимается
отдельный сервер prometheus_client на METRICS_PORT (Prometheus scrape'ит его
отдельным job'ом, см. prometheus.yml).
"""
import logging

from prometheus_client import start_http_server
from rq import Queue, SimpleWorker

from app.redis_conn import redis_conn

logging.basicConfig(level=logging.INFO)

METRICS_PORT = 8001

if __name__ == "__main__":
    start_http_server(METRICS_PORT)
    queue = Queue("checks", connection=redis_conn)
    worker = SimpleWorker([queue], connection=redis_conn)
    worker.work()
