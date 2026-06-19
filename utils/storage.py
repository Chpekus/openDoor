"""
Система управления хранилищем скриншотов
Структура: YEAR/MONTH/DAY/screenshot.png
"""
import os
from datetime import datetime
from pathlib import Path
from utils.logger import log_error, log_info

SCREENSHOTS_ROOT = Path("screenshot_of_open")
MEDIA_EXTENSIONS = (".png", ".webm")


def get_screenshot_path(timestamp=None, gesture_names=None, extension=".png"):
    """
    Генерирует путь для сохранения скриншота
    
    Args:
        timestamp: datetime объект (если None, используется текущее время)
        gesture_names: список названий жестов (опционально)
    
    Returns:
        Path объект к файлу скриншота
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    # Создаём структуру: year/month/day
    year = timestamp.strftime("%Y")
    month = timestamp.strftime("%m")
    day = timestamp.strftime("%d")
    
    dir_path = SCREENSHOTS_ROOT / year / month / day
    
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        log_info("storage", f"Created directory: {dir_path}")
    except Exception as e:
        log_error("storage", f"Failed to create directory {dir_path}: {e}")
        raise
    
    # Генерируем имя файла
    time_str = timestamp.strftime("%H-%M-%S")
    
    if gesture_names:
        gesture_str = "+".join(gesture_names[:3])  # Максимум 3 жеста в имени
        filename = f"{time_str}_{gesture_str}{extension}"
    else:
        filename = f"{time_str}{extension}"
    
    return dir_path / filename


def get_day_screenshots(year, month, day, max_count=6):
    """
    Получает скриншоты для конкретного дня (максимум max_count)
    
    Args:
        year: год (2026)
        month: месяц (01-12)
        day: день (01-31)
        max_count: максимальное количество скриншотов
    
    Returns:
        список путей к файлам скриншотов
    """
    day_dir = SCREENSHOTS_ROOT / f"{year}" / f"{month}" / f"{day}"
    
    if not day_dir.exists():
        return []
    
    try:
        # Получаем все PNG файлы в директории, отсортированные по времени
        screenshots = sorted(
            file_path for file_path in day_dir.iterdir()
            if file_path.is_file() and file_path.suffix.lower() in MEDIA_EXTENSIONS
        )
        
        # Возвращаем только максимум max_count
        return screenshots[-max_count:]
    except Exception as e:
        log_error("storage", f"Failed to get screenshots from {day_dir}: {e}")
        return []


def get_calendar_data(year, month):
    """
    Получает данные для календаря (какие дни имеют скриншоты)
    
    Args:
        year: год
        month: месяц (01-12)
    
    Returns:
        dict: {day: count_screenshots, ...}
    """
    month_dir = SCREENSHOTS_ROOT / f"{year}" / f"{month}"
    
    if not month_dir.exists():
        return {}
    
    calendar_data = {}
    
    try:
        # Проходим по всем дням в месяце
        for day_dir in month_dir.iterdir():
            if day_dir.is_dir():
                day = day_dir.name
                screenshots = [
                    file_path for file_path in day_dir.iterdir()
                    if file_path.is_file() and file_path.suffix.lower() in MEDIA_EXTENSIONS
                ]
                if screenshots:
                    calendar_data[day] = len(screenshots)
    except Exception as e:
        log_error("storage", f"Failed to get calendar data for {year}/{month}: {e}")
    
    return calendar_data


def cleanup_old_screenshots(days_to_keep=90):
    """
    Удаляет старые скриншоты (старше чем days_to_keep дней)
    
    Args:
        days_to_keep: количество дней для хранения
    """
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    try:
        for year_dir in SCREENSHOTS_ROOT.iterdir():
            if not year_dir.is_dir():
                continue
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                for day_dir in month_dir.iterdir():
                    if not day_dir.is_dir():
                        continue
                    
                    try:
                        day_date = datetime.strptime(f"{year_dir.name}-{month_dir.name}-{day_dir.name}", "%Y-%m-%d")
                        if day_date < cutoff_date:
                            import shutil
                            shutil.rmtree(day_dir)
                            log_info("storage", f"Deleted old directory: {day_dir}")
                    except ValueError:
                        pass
    except Exception as e:
        log_error("storage", f"Cleanup failed: {e}")


def get_screenshot_info(file_path):
    """
    Парсит информацию из имени файла скриншота
    
    Args:
        file_path: путь к файлу скриншота
    
    Returns:
        dict: {time: "14:35:22", gestures: ["TiDishi", "Rock"], ...}
    """
    try:
        filename = Path(file_path).stem  # Получаем имя файла без расширения
        
        # Формат: HH-MM-SS_Gesture1+Gesture2
        if "_" in filename:
            time_str, gestures_str = filename.split("_", 1)
            gestures = gestures_str.split("+")
        else:
            time_str = filename
            gestures = []
        
        return {
            "time": time_str.replace("-", ":"),
            "gestures": gestures
        }
    except Exception as e:
        log_error("storage", f"Failed to parse screenshot info from {file_path}: {e}")
        return {"time": "", "gestures": []}
