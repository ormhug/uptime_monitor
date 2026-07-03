# Uptime Monitor

[![CI](https://github.com/ormhug/uptime_monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/ormhug/uptime_monitor/actions/workflows/ci.yml)

<!--
Бейдж подставлен под текущий remote (ormhug/uptime_monitor, см. `git remote -v`).
Если репозиторий переименуют или форкнут — поменяй owner/repo в обеих ссылках
на `<owner>/<repo>` из своего GitHub-URL.
-->

Мини-аналог UptimeRobot/BetterStack: добавляешь URL, сервис периодически проверяет
доступность и хранит историю проверок.

Архитектура: FastAPI (API) → Postgres (мониторы и история) + Redis/RQ (очередь) →
отдельный воркер, который и выполняет проверки. Подробности — в [CLAUDE.md](CLAUDE.md).

## Быстрый старт через Docker Compose

Нужен установленный Docker и Docker Compose.

```bash
docker compose up --build
```

Поднимет 4 сервиса: `postgres`, `redis`, `api` (порт 8000), `worker`.

Применить миграции (один раз после первого поднятия, и затем после каждой новой миграции):

```bash
docker compose exec api alembic upgrade head
```

Проверить, что всё работает: [http://localhost:8000/docs](http://localhost:8000/docs) — Swagger UI,
можно сразу создать монитор через `POST /monitors`.

Логи конкретного сервиса (например, воркера — там видно, как выполняются проверки):

```bash
docker compose logs -f worker
```

Остановить и убрать контейнеры (данные Postgres в volume `postgres_data` сохранятся):

```bash
docker compose down
```

Добавить `-v` к `down`, если нужно снести и данные Postgres тоже.

## Локальный запуск без Docker

Для разработки и тестов можно обойтись без Docker — тогда нужны локально запущенные
Postgres и Redis, и venv проекта.

```bash
.venv\Scripts\activate.bat
copy .env.example .env
# отредактировать .env — вписать реальные DATABASE_URL/REDIS_URL

alembic upgrade head

# терминал 1 — API
uvicorn app.main:app --reload

# терминал 2 — воркер
python -m app.worker
```

## Тесты

```bash
pytest -v
```

Тесты используют SQLite in-memory и не трогают рабочую БД — подробности в
[CLAUDE.md](CLAUDE.md#тестирование).
