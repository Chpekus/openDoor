"""
Система логирования с временем для всего приложения
"""
import logging
import os
from datetime import datetime
from pathlib import Path

# Создаём папку для логов
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Форматер с временем
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def setup_logger(name, log_file=None):
    """
    Настраивает логгер с обработчиками для консоли и файла
    
    Args:
        name: имя логгера
        log_file: имя файла лога (опционально)
    
    Returns:
        объект логгера
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Консоль (WARNING и выше)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файл (все уровни)
    if log_file is None:
        log_file = f"{name}.log"
    
    file_path = LOGS_DIR / log_file
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# Глобальные логгеры
logger_main = setup_logger("main", "main.log")
logger_worker = setup_logger("worker", "worker.log")
logger_recognition = setup_logger("recognition", "recognition.log")
logger_door = setup_logger("door_open", "door_open.log")
logger_database = setup_logger("database", "database.log")
logger_app = setup_logger("app", "app.log") 


def log_door_open(image_path, gestures, response_code, response_text):
    """Логирует события открытия двери"""
    logger_door.info(
        f"DOOR OPENED | Path: {image_path} | Gestures: {gestures} | "
        f"Code: {response_code} | Response: {response_text[:100]}"
    )


def log_error(logger_name, message, exc_info=False):
    """Логирует ошибку"""
    logger = logging.getLogger(logger_name)
    logger.error(message, exc_info=exc_info)


def log_warning(logger_name, message):
    """Логирует предупреждение"""
    logger = logging.getLogger(logger_name)
    logger.warning(message)


def log_info(logger_name, message):
    """Логирует информацию"""
    logger = logging.getLogger(logger_name)
    logger.info(message)
