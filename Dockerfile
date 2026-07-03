# Образ для процесса API (uvicorn + FastAPI).
# slim — минимальный образ Debian с Python, без лишних инструментов сборки.
FROM python:3.12-slim

# не писать .pyc-файлы и не буферизовать stdout/stderr — логи сразу видны через docker logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# сначала копируем только requirements.txt и ставим зависимости — этот слой
# кэшируется Docker'ом и пересобирается только при изменении зависимостей,
# а не при каждом изменении кода приложения
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# теперь копируем код приложения (.dockerignore исключает .venv, тесты, .env и т.п.)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
