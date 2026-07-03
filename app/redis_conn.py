"""
Подключение к Redis — брокеру очереди задач (RQ).
"""
import os

from dotenv import load_dotenv
from redis import Redis

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# соединение лениво: реального обращения к Redis не происходит до первой команды
redis_conn = Redis.from_url(REDIS_URL)
