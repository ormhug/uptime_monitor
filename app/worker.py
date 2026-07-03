"""
Точка входа RQ-воркера — отдельный процесс, слушающий очередь Redis и
выполняющий задачи проверки мониторов (app/tasks.py::run_check).

Запуск (из корня проекта, при активном .venv):
    python -m app.worker

Используется SimpleWorker, а не стандартный rq.Worker: обычный Worker форкает
дочерний процесс (os.fork) на каждую задачу, а на Windows fork недоступен.
SimpleWorker выполняет задачи в своём же процессе — этого достаточно для
дев-окружения на этом этапе (без изоляции падений между задачами).
"""
import logging

from rq import Queue, SimpleWorker

from app.redis_conn import redis_conn

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    queue = Queue("checks", connection=redis_conn)
    worker = SimpleWorker([queue], connection=redis_conn)
    worker.work()
