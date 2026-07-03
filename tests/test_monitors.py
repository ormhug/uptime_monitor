"""
Тесты для эндпоинтов /monitors.
"""


async def test_create_monitor(client):
    """Создание монитора с валидным URL возвращает 201 и объект с id."""
    response = await client.post(
        "/monitors",
        json={"url": "https://example.com", "name": "Example"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] is not None
    assert body["name"] == "Example"
    assert body["url"].startswith("https://example.com")
    assert body["is_active"] is True
    assert body["last_checked_at"] is None


async def test_create_monitor_invalid_url(client):
    """Невалидный URL отклоняется Pydantic-валидацией с 422."""
    response = await client.post(
        "/monitors",
        json={"url": "not-a-url", "name": "Bad"},
    )

    assert response.status_code == 422


async def test_get_monitors_empty(client):
    """На пустой базе список мониторов пуст."""
    response = await client.get("/monitors")

    assert response.status_code == 200
    assert response.json() == []


async def test_get_monitors_after_create(client):
    """После создания монитор появляется в общем списке."""
    await client.post("/monitors", json={"url": "https://example.com", "name": "Example"})

    response = await client.get("/monitors")

    assert response.status_code == 200
    monitors = response.json()
    assert len(monitors) == 1
    assert monitors[0]["name"] == "Example"


async def test_get_nonexistent_monitor_history(client):
    """История несуществующего монитора — 404."""
    response = await client.get("/monitors/999/history")

    assert response.status_code == 404


async def test_monitor_status_no_checks_yet(client):
    """
    Монитор существует, но проверок ещё не было (scheduler не успел отработать).

    Это не ошибка — 404 тут был бы неверен, ведь сам монитор найден.
    Разумное поведение: 200 с last_result=None и uptime_percent_24h=0.0,
    т.к. отсутствие данных за период — это 0% подтверждённого аптайма,
    а не "сайт не работает" и не "монитор не найден".
    """
    create_response = await client.post("/monitors", json={"url": "https://example.com", "name": "Example"})
    monitor_id = create_response.json()["id"]

    response = await client.get(f"/monitors/{monitor_id}/status")

    assert response.status_code == 200
    body = response.json()
    assert body["monitor_id"] == monitor_id
    assert body["last_result"] is None
    assert body["uptime_percent_24h"] == 0.0
