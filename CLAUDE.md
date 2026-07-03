# CLAUDE.md — Uptime Monitor

Этот файл — постоянный контекст проекта для Claude Code. Читай перед началом работы.

## О проекте

Пет-проект: сервис мониторинга аптайма (мини-аналог UptimeRobot / BetterStack).
Пользователь добавляет URL, сервис периодически проверяет доступность и уведомляет при падении.

Цели проекта:
- Портфолио для резюме / собеседований
- Потенциальная монетизация в будущем (SaaS)

Автор — студент, знает основы backend, учится глубже в backend + devops.

## Стек

- Python 3.x, FastAPI, Uvicorn
- SQLAlchemy + Alembic (миграции)
- PostgreSQL — хранение мониторов и истории проверок
- Redis + RQ — очередь задач для проверок (API ставит задачи, воркер выполняет)
- venv лежит в `.venv/` в корне проекта, установлен и активен

Установленные пакеты на старте:
```
fastapi uvicorn sqlalchemy alembic psycopg2-binary python-dotenv
```

## Архитектура (реализовано на Этапе 2)

```
Клиент → API (FastAPI) → Postgres (хранит мониторы и историю)
                        → Redis (очередь задач, RQ)
                              ↓
                          Worker (app/worker.py, RQ SimpleWorker)
                              ↓
                   пишет результат в Postgres (уведомления — позже)
```

API и Worker — разные процессы, общаются только через Redis (очередь) и Postgres (общая БД),
напрямую друг с другом не взаимодействуют:

- Внутри процесса API работает APScheduler (`app/scheduler.py`) — раз в 30 сек берёт активные
  мониторы и **ставит задачу в очередь RQ** (`queue.enqueue(run_check, monitor.id)`), сам проверку
  не выполняет.
- Задача — вызов `app/tasks.py::run_check(monitor_id)`: открывает свою сессию БД (не через
  `Depends`, т.к. это не HTTP-контекст), вызывает `check_url()`, сохраняет `CheckResult`,
  обновляет `last_checked_at`.
- Воркер (`app/worker.py`) — отдельный процесс, слушает очередь `checks` в Redis и выполняет
  задачи по мере поступления. Используется `SimpleWorker` вместо обычного `rq.Worker`, потому что
  стандартный `Worker` форкает дочерний процесс (`os.fork`) на каждую задачу, а на Windows fork
  недоступен.

### Запуск через Docker Compose (рекомендуется, Этап 3)

Поднимает разом все 4 сервиса — `postgres`, `redis`, `api`, `worker`:

```bash
docker compose up --build
```

Миграции применяются вручную внутри контейнера api (один раз после первого поднятия
и затем после каждой новой миграции):

```bash
docker compose exec api alembic upgrade head
```

Логи конкретного сервиса: `docker compose logs -f worker` (или `api`/`postgres`/`redis`).
Остановить всё: `docker compose down` (данные Postgres остаются в volume `postgres_data`;
`docker compose down -v`, если нужно снести и их тоже).

Переменные окружения (`DATABASE_URL`, `REDIS_URL`) заданы прямо в `docker-compose.yml`
(блок `x-app-env`) и указывают на **имена сервисов** (`postgres`, `redis`), а не на `localhost` —
внутри контейнера `api` `localhost` означал бы сам контейнер `api`, где нет ни Postgres, ни
Redis. Docker Compose поднимает все сервисы в общей сети и резолвит их имена через встроенный
DNS, поэтому контейнеры обращаются друг к другу по имени сервиса. Файл `.env` в этом сценарии
не используется — он нужен только для запуска без Docker (см. ниже).

Подробности — в [README.md](README.md).

### Запуск вручную, без Docker (для локальной разработки и тестов)

Нужны ОБА процесса одновременно плюс локально поднятые Postgres и Redis:

```bash
# терминал 1 — API
uvicorn app.main:app --reload

# терминал 2 — воркер
python -m app.worker
```

Postgres и Redis должны быть подняты и доступны по `DATABASE_URL` / `REDIS_URL` из `.env`.

Как проверить, что задача реально прошла через Redis к воркеру (что через Docker Compose, что
вручную): создать монитор через `POST /monitors`, подождать один тик планировщика (до 30 сек)
и посмотреть логи — в логе API появится `монитор N поставлен в очередь на проверку`, а в логе
воркера — `checks: app.tasks.run_check(N) (...)` и затем `monitor N (...): up/down [код], N мс`.
Результат также должен появиться в `GET /monitors/{id}/history`.

## Структура проекта (целевая)

```
uptime-monitor/
├── app/
│   ├── main.py          # точка входа FastAPI, lifespan запускает scheduler (постановку задач)
│   ├── models.py        # SQLAlchemy модели: Monitor, CheckResult
│   ├── database.py      # подключение к Postgres
│   ├── redis_conn.py    # подключение к Redis (брокер очереди RQ)
│   ├── schemas.py       # Pydantic схемы
│   ├── checker.py       # проверка доступности одного URL (httpx)
│   ├── scheduler.py     # APScheduler-джоб: раз в 30 сек ставит проверки в очередь RQ
│   ├── tasks.py         # run_check(monitor_id) — задача, которую выполняет воркер
│   ├── worker.py        # точка входа RQ-воркера (python -m app.worker)
│   └── routers/
│       └── monitors.py  # эндпоинты для мониторов
├── Dockerfile            # образ API (uvicorn)
├── Dockerfile.worker      # образ воркера (RQ SimpleWorker)
├── docker-compose.yml     # postgres + redis + api + worker одной командой
├── .dockerignore
├── requirements.txt
├── README.md
└── .env
```

## Текущий статус

- [x] Создано окружение `.venv` в папке проекта (`PetProject`, Windows)
- [x] Установлены базовые пакеты (см. выше)
- [x] Структура папок `app/` создана
- [x] Подключение к Postgres (`database.py`)
- [x] Модель `Monitor` (`models.py`)
- [x] Pydantic-схемы (`schemas.py`)
- [x] Первые эндпоинты: `POST /monitors`, `GET /monitors`
- [x] Alembic инициализирован, первая миграция создана (`monitors`)
- [x] Модель `CheckResult` + поле `Monitor.last_checked_at`, миграция применена
- [x] Проверка доступности сайта (`checker.py`, через httpx)
- [x] Фоновый планировщик проверок (`scheduler.py`, APScheduler, раз в 30 сек, запускается через lifespan в `main.py`)
- [x] Эндпоинты `GET /monitors/{id}/history` и `GET /monitors/{id}/status` (uptime % за 24ч)
- [x] Тесты pytest для API и checker.py (`tests/`), не трогают рабочую БД

**Этап 1 полностью закрыт.**

- [x] Redis как брокер очереди задач (`redis_conn.py`, `REDIS_URL` в `.env`)
- [x] Проверки вынесены из планировщика в задачу очереди (`tasks.py::run_check`)
- [x] `scheduler.py` теперь только ставит задачи в очередь (RQ `enqueue`), не выполняет их сам
- [x] Отдельный процесс-воркер (`worker.py`, RQ `SimpleWorker` — Windows-совместимость, без `os.fork`)
- [x] Проверено вживую: API → Redis → Worker → Postgres, по логам обоих процессов
- [x] Тест `tests/test_tasks.py::run_check` (замокан `check_url`, подменена сессия БД)

**Этап 2 полностью закрыт.**

- [x] `Dockerfile` (API, python:3.12-slim, uvicorn) и `Dockerfile.worker` (тот же образ, CMD воркера)
- [x] `docker-compose.yml`: postgres (с volume) + redis + api + worker, переменные окружения
      на имена сервисов, а не localhost
- [x] `.dockerignore` (.venv, __pycache__, .git, tests, .env)
- [x] `README.md` с инструкцией по запуску через compose и локально
- [x] Проверено вживую: `docker compose up --build`, миграции внутри контейнера, монитор
      прошёл полный путь API → Redis → Worker → Postgres (и up, и down статус)
- [x] Локальный запуск без Docker (venv, `pytest`) по-прежнему работает — не сломан

**Этап 3 полностью закрыт.**

- [x] `.github/workflows/ci.yml`: job `test` (checkout → Python 3.12 → кэш pip по хэшу
      requirements.txt → `pip install` → `pytest -v`) и job `docker-build` (сборка Dockerfile и
      Dockerfile.worker, без push), `docker-build` запускается только после успешного `test`
- [x] CI не поднимает Postgres/Redis — тесты полностью на SQLite in-memory (уже так было
      настроено в `tests/conftest.py`), проверено локально: `pytest -v` зелёный даже без файла
      `.env` вообще (в CI его и не будет — он в `.gitignore`)
- [x] CI-бейдж в README.md (реальный репозиторий `ormhug/uptime_monitor`)
- [x] Проверено вживую: чистый venv + `pip install -r requirements.txt` + `pytest -v` (11/11),
      плюс `docker build` для обоих Dockerfile — те же команды, что выполнит workflow

**Этап 4 полностью закрыт.**

## Roadmap (полный, по этапам)

1. ~~**Голый backend без очереди.** Один процесс FastAPI + простой cron/scheduler для проверок.~~ ✅ завершён
2. ~~**Разделение на сервисы.** Выносим проверки в отдельный воркер, добавляем Redis как очередь задач.~~ ✅ завершён (API + Redis/RQ + воркер, см. раздел "Архитектура" выше)
3. ~~**Контейнеризация.** Docker + docker-compose для API, воркера, Postgres, Redis.~~ ✅ завершён
4. ~~**CI/CD.** GitHub Actions: тесты → билд.~~ ✅ завершён (см. раздел "CI/CD" ниже)
5. **Мониторинг** — текущий этап. Prometheus + Grafana для метрик самого сервиса.
6. **Продакшен-детали** — HTTPS, JWT-аутентификация, rate limiting, Sentry, опционально Kubernetes.

## Тестирование

Запуск: `pytest -v` (из корня проекта, при активном `.venv`).

- Тестовая БД — SQLite in-memory (`tests/conftest.py`), не Postgres. Модели используют только
  переносимые типы SQLAlchemy, так что реальная Postgres для тестов не нужна. `get_db`
  подменяется через `app.dependency_overrides`, рабочая база не затрагивается никогда.
- Перед каждым тестом таблицы создаются заново, после — удаляются (фикстура `clean_db`, autouse).
- `tests/test_monitors.py` — API-эндпоинты: создание монитора (валидный/невалидный URL),
  список мониторов, 404 для несуществующего монитора, статус монитора без единой проверки.
  Запросы идут через `httpx.AsyncClient` + `ASGITransport` (без реального сервера).
- `tests/test_checker.py` — логика `check_url()` с замоканным `httpx.get` (успех, код 5xx, таймаут),
  без реальных сетевых запросов.
- `tests/test_tasks.py` — логика `tasks.run_check()`: сохраняет `CheckResult` и обновляет
  `last_checked_at` (check_url замокан), плюс случай удалённого монитора (не падает). Сессия БД
  подменена на тестовую через `@patch("app.tasks.SessionLocal", TestingSessionLocal)`.
- Планировщик (`scheduler.py`) и воркер (`worker.py`, RQ) намеренно не тестируются напрямую —
  сама логика проверки уже покрыта тестами tasks.py/checker.py, а тестировать APScheduler/RQ
  имитацией времени и очереди избыточно для этого этапа. Реальное прохождение задачи через
  Redis к воркеру проверялось вручную (см. раздел "Архитектура" выше).

## CI/CD

Workflow — `.github/workflows/ci.yml`, триггерится на каждый `push` и `pull_request` в `main`.

- **Job `test`** — Python 3.12, кэш pip-пакетов по хэшу `requirements.txt`, `pip install -r
  requirements.txt`, затем `pytest -v`. Postgres/Redis в CI не поднимаются и не нужны — тесты
  используют SQLite in-memory (см. раздел "Тестирование" выше), а `check_url`/HTTP замокан.
- **Job `docker-build`** — запускается только если `test` прошёл (`needs: test`). Собирает
  `Dockerfile` и `Dockerfile.worker` (`docker build`, без push куда-либо) — цель только
  убедиться, что оба образа реально собираются, а не что они рабочие end-to-end (это уже
  проверено вручную на Этапе 3).
- Результат виден во вкладке **Actions** репозитория на GitHub, а также бейджем в README.md.
  Если тест или сборка образа падают — соответствующий job/шаг подсвечивается красным, в PR
  появляется failed-статус-чек, и по клику на бейдж/Actions видно точный лог упавшего шага.
- Дальше на будущее (не реализовано намеренно, отдельный шаг): автодеплой после успешного CI
  (например, на этап 6 — сборка и push образов в registry + деплой), линтер/форматтер как
  отдельный job, покрытие тестами (`pytest --cov`).

## Конвенции разработки

- Объяснения и комментарии в коде — на русском, если не оговорено иначе
- Приоритет: сначала простое рабочее решение, потом рефакторинг
- Коммитить часто, вести содержательный README
- Не переусложнять раньше времени — очередь/Docker/CI добавляются только на соответствующих этапах, не раньше

## Окружение (напоминание)

- Активация venv (Windows): `.venv\Scripts\activate.bat`
- Интерпретатор в VS Code выбран через `Python: Select Interpreter`
