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

Поднимет 6 сервисов: `postgres`, `redis`, `api` (порт 8000), `worker`, `prometheus` (порт 9090),
`grafana` (порт 3000).

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

## Мониторинг (Prometheus + Grafana)

- **Prometheus** — [http://localhost:9090](http://localhost:9090). Раз в 15 сек ходит на
  `api:8000/metrics` и `worker:8001/metrics` (см. `prometheus.yml`). Проверить, что таргеты
  живы: Status → Targets. Посмотреть сырые метрики вручную: вкладка Graph, в поле запроса —
  например `monitor_checks_total` или `active_monitors_total`, кнопка Execute (таб Table
  покажет текущие значения по всем лейблам, таб Graph — график во времени).
- **Grafana** — [http://localhost:3000](http://localhost:3000), логин/пароль по умолчанию
  `admin` / `admin` (при первом входе может попросить сменить пароль — можно пропустить).
  Datasource на Prometheus подключается автоматически при старте (провижининг из
  `grafana/provisioning/datasources/`), проверить: Connections → Data sources → должен
  быть источник "Prometheus". Если по какой-то причине его нет — добавить вручную:
  Connections → Data sources → Add data source → Prometheus → URL `http://prometheus:9090` → Save & test.
  Дашборды (графики/панели) сюда не входят — их предполагается собирать вручную через UI
  (Dashboards → New → Add visualization → выбрать datasource Prometheus → вписать запрос,
  например `rate(monitor_checks_total[5m])`).

Доступные метрики:

- `active_monitors_total` — сколько сейчас активных мониторов (Gauge, обновляется в
  `scheduler.py` раз в 30 сек). Смотреть с job="api" — в job="worker" эта же метрика тоже
  видна из-за общего импорта `app/metrics.py`, но там всегда 0 (никогда не выставляется
  в процессе воркера).
- `monitor_checks_total{status="up"|"down"}` — сколько проверок и с каким исходом (Counter).
  Живёт только на `worker:8001/metrics` — сама проверка (`run_check`) выполняется в процессе
  воркера, а метрики `prometheus_client` хранятся в памяти процесса, поэтому у воркера свой
  отдельный `/metrics`-эндпоинт (порт 8001), не тот же самый, что у API.
- `monitor_check_duration_seconds` — длительность одной проверки (Histogram), тоже только
  на `worker:8001/metrics`.
- Стандартные HTTP-метрики API (`http_requests_total`, латентность и т.д.) — от
  `prometheus-fastapi-instrumentator`, на `api:8000/metrics`.

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
