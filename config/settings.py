"""
Централизованная конфигурация приложения
"""
import os
from dotenv import load_dotenv

load_dotenv()

# === БД ===
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("PGDATABASE", "opendoor")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "")

# === API Новотелеком ===
LOGIN = os.getenv("LOGIN", "")
PASSWORD = os.getenv("PASSWORD", "")
BEARER_TOKEN = os.getenv("bearer_token", "")

# === Веб-сервис ===
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")

# === Интерком ===
INTERCOM_ID = int(os.getenv("INTERCOM_ID", "3104703"))

# === Распознавание ===
GESTURE_MIN_DETECTION_CONFIDENCE = 0.5
GESTURE_MIN_TRACKING_CONFIDENCE = 0.5
GESTURE_MAX_HANDS = 1

# === Обработка видео ===
FRAME_SKIP_RATE = 2  # Обрабатываем каждый N-й кадр
GESTURE_WINDOW_SIZE = 20  # Окно для поиска жестов
GESTURE_COMBO_REQUIRED = {
    "TiDishi": 5,  # 5 жестов TiDishi
    "Rock": 2      # 2 жеста Rock
}
DOOR_OPEN_COOLDOWN = 7  # Минимум секунд между открытиями

# === Хранилище ===
SCREENSHOT_MAX_PER_DAY = 6
SCREENSHOT_DAYS_TO_KEEP = 90

# === Стрим ===
STREAM_LIFETIME = 1440  # Секунды

# === Пользователи (для авторизации) ===
USERS = {
    "admin": "admin123",  # Измените на нормальный пароль в .env
    "user": "user123"
}
