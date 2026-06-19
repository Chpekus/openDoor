"""
Рабочие потоки для обработки асинхронных задач
"""
from queue import Queue
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import cv2
from pathlib import Path
from datetime import datetime

from config.settings import PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD, BEARER_TOKEN
from utils.logger import log_info, log_warning, log_error, log_door_open
from db.database import Database, insert_gesture, insert_door_open
from services.novotelecom import send_post_open_door_request, make_session, get_stream_url

task_queue = Queue()

OPEN_CLIP_FPS = 5
OPEN_CLIP_MAX_WIDTH = 640


@dataclass
class Task:
    kind: str                  # тип задачи
    data: Dict[str, Any]       # аргументы
    need_result: bool = False  # ждать ли результат
    result: Any = None
    event: threading.Event = field(default_factory=threading.Event)


def save_webm_clip(frames, path, fps=OPEN_CLIP_FPS, max_width=OPEN_CLIP_MAX_WIDTH):
    if not frames:
        raise ValueError("No frames to save")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    normalized_frames = []
    for frame in frames:
        if frame is None:
            continue

        height, width = frame.shape[:2]
        if width > max_width:
            scale = max_width / width
            frame = cv2.resize(frame, (max_width, int(height * scale)))
            height, width = frame.shape[:2]

        even_width = width - (width % 2)
        even_height = height - (height % 2)
        if (even_width, even_height) != (width, height):
            frame = cv2.resize(frame, (even_width, even_height))

        normalized_frames.append(frame)

    if not normalized_frames:
        raise ValueError("No valid frames to save")

    height, width = normalized_frames[0].shape[:2]
    size = (width, height)

    for codec in ("VP90", "VP80"):
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*codec),
            fps,
            size
        )
        if not writer.isOpened():
            writer.release()
            continue

        try:
            for frame in normalized_frames:
                if frame.shape[:2] != (height, width):
                    frame = cv2.resize(frame, size)
                writer.write(frame)
        finally:
            writer.release()

        if path.exists() and path.stat().st_size > 0:
            return path

    raise RuntimeError("OpenCV could not encode WebM with VP9 or VP8")


def io_worker():
    """
    Основной рабочий поток для выполнения задач ввода-вывода:
    - Открытие двери
    - Получение сеансов
    - Получение URL потоков
    - Сохранение скриншотов
    - Вставка в БД
    """
    log_info("worker", "IO Worker started")
    
    try:
        while True:
            task: Task = task_queue.get()
            try:
                if task.kind == "open_door":
                    token = task.data["token"]
                    screenshot_path = task.data.get("path")
                    gestures = task.data.get("gestures", [])
                    
                    status_code, body = send_post_open_door_request(token)
                    if task.need_result:
                        task.result = {
                            "status_code": status_code,
                            "body": body
                        }
                    
                    # Логируем открытие двери с временем
                    log_door_open(screenshot_path, gestures, status_code, body)
                    
                    # Вставляем в БД
                    insert_door_open(screenshot_path, status_code, body)
                    
                    log_info("worker", f"Door opened: {status_code}")

                elif task.kind == "get_stream_url":
                    session = task.data["session"]    
                    id_intercom = task.data["id_intercom"]
                    url = get_stream_url(session=session, id_intercom=id_intercom)
                    if task.need_result:
                        task.result = url
                    log_info("worker", f"Stream URL obtained for intercom {id_intercom}")
            
                elif task.kind == "get_website_session":
                    session = make_session()
                    if task.need_result:
                        task.result = session
                    log_info("worker", "Website session created")

                elif task.kind == "save_screenshot":
                    frame = task.data["frame"]     # np.array (BGR)
                    path = task.data["path"]
                    
                    # Создаём родительскую директорию если её нет
                    Path(path).parent.mkdir(parents=True, exist_ok=True)
                    
                    cv2.imwrite(path, frame)
                    log_info("worker", f"Screenshot saved: {path}")

                elif task.kind == "save_open_clip":
                    frames = task.data["frames"]
                    path = task.data["path"]

                    save_webm_clip(frames, path)
                    log_info("worker", f"Opening clip saved: {path}")

                elif task.kind == "db_insert_gesture":
                    gesture = task.data["gesture"]
                    insert_gesture(gesture)

                elif task.kind == "db_insert":
                    # Устаревший формат, поддерживаем для совместимости
                    sql = task.data["sql"]
                    params = task.data["params"]
                    if not isinstance(params, (tuple, list)):
                        params = (params,)
                    
                    db = Database()
                    db.execute(sql, tuple(params))
                    db.close()

            except Exception as e:
                if task.need_result:
                    task.result = {
                        "status_code": None,
                        "body": str(e),
                        "error": True
                    }
                log_error("worker", f"Error processing task {task.kind}: {e}", exc_info=True)
            finally:
                if task.need_result:
                    task.event.set()
                task_queue.task_done()
    
    except Exception as e:
        log_error("worker", f"Fatal error in IO worker: {e}", exc_info=True)


def start_io_workers(n=1):
    """Запускает N рабочих потоков"""
    workers = []
    for i in range(n):
        t = threading.Thread(target=io_worker, daemon=True)
        t.start()
        workers.append(t)
        log_info("worker", f"Started IO worker {i+1}/{n}")
    return workers
