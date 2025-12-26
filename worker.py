from queue import Queue
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import novotelecom_integrarion
import cv2
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

task_queue = Queue()

@dataclass
class Task:
    kind: str                  # тип задачи: 'open_door', 'get_stream_url'...
    data: Dict[str, Any]       # аргументы
    need_result: bool = False  # ждать ли результат
    result: Any = None
    event: threading.Event = field(default_factory=threading.Event)


def io_worker():
    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD")
    )
    conn.autocommit = True

    while True:
        task: Task = task_queue.get()
        try:
            if task.kind == "open_door":
                token = task.data["token"]
                screenshot_path = task.data.get("path")
                status_code, body = novotelecom_integrarion.send_post_open_door_request(token)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO case_of_open(img_path, response_code, response_text)
                        VALUES (%s, %s, %s)
                        """,
                        (str(screenshot_path), status_code, str(body))
                    )

            elif task.kind == "get_stream_url":
                if "session" in task.data:
                    session = task.data["session"]
                    url, session = novotelecom_integrarion.get_stream_url_via_requests(session)
                else:
                    login = task.data["login"]
                    password = task.data["password"]
                    url, session = novotelecom_integrarion.get_stream_url_via_requests(login, password)
                if task.need_result:
                    task.result = url, session

            elif task.kind == "save_screenshot":
                frame = task.data["frame"]     # np.array (BGR)
                path = task.data["path"]
                cv2.imwrite(path, frame)

            elif task.kind == "db_insert":
                sql = task.data["sql"]
                params = task.data["params"]
                if not isinstance(params, (tuple, list)):
                    params = (params,)
                with conn.cursor() as cur:
                    cur.execute(sql, tuple(params))

            

        except Exception as e:
            print(f"Ошибка в io_worker для задачи {task.kind}: {e} {task.data}")
        finally:
            if task.need_result:
                task.event.set()
            task_queue.task_done()
