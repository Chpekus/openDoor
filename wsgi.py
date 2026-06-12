"""
WSGI entry point для Gunicorn
Запуск: gunicorn --bind 0.0.0.0:8000 wsgi:app
"""

import sys
import os
import threading
import time

# Добавляем текущую директорию в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import log_info, log_error
from services.worker import start_io_workers
from core.analyzer import start_processing_thread
from app.routes import app

# Запускаем компоненты при старте
def init_app():
    """Инициализация приложения при запуске"""
    try:
        log_info("main", "=" * 50)
        log_info("main", "Initializing OpenDoor Service")
        log_info("main", "=" * 50)
        
        # Запускаем рабочие потоки
        log_info("main", "Starting IO workers...")
        start_io_workers(n=1)
        time.sleep(1)
        
        # Запускаем поток обработки видео
        log_info("main", "Starting video processing thread...")
        start_processing_thread()
        time.sleep(1)
        
        log_info("main", "OpenDoor Service initialized successfully")
    except Exception as e:
        log_error("main", f"Failed to initialize OpenDoor: {e}", exc_info=True)
        raise

# Инициализируем при импорте модуля
init_app()

if __name__ == '__main__':
    # Для локального тестирования (НЕ используйте в production!)
    log_info("main", "Running in debug mode (use gunicorn in production)")
    app.run(host='127.0.0.1', port=8000, debug=False, use_reloader=False)
