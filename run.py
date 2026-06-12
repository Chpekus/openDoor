#!/usr/bin/env python3
"""
Главный entry point приложения OpenDoor
Запускает:
1. Поток обработки видео (core/analyzer.py)
2. Рабочие потоки для обработки задач (services/worker.py)
3. Flask веб-приложение (app/routes.py)
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


def main():
    """Главная функция приложения"""
    log_info("main", "=" * 50)
    log_info("main", "Starting OpenDoor Service")
    log_info("main", "=" * 50)
    
    # Запускаем рабочие потоки (для обработки очереди задач)
    log_info("main", "Starting IO workers...")
    start_io_workers(n=1)
    time.sleep(1)
    
    # Запускаем поток обработки видео
    log_info("main", "Starting video processing thread...")
    start_processing_thread()
    time.sleep(2)
    
    # Запускаем Flask приложение
    log_info("main", "Starting Flask web application...")
    from app.routes import app
    from config.settings import WEB_HOST, WEB_PORT
    
    try:
        app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
    except Exception as e:
        log_error("main", f"Failed to start Flask app: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()


if __name__ == "__main__":
    main()
