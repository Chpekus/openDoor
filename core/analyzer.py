"""
Основной цикл обработки видеопотока и распознавания жестов
"""
import time
from datetime import datetime
import math
import random
import threading

import cv2
import numpy as np
import mediapipe as mp
import json
from collections import deque

from core.recognition import classify_gesture
from services.worker import task_queue, Task
from config.settings import (
    LOGIN, PASSWORD, BEARER_TOKEN, INTERCOM_ID,
    GESTURE_MIN_DETECTION_CONFIDENCE, GESTURE_MIN_TRACKING_CONFIDENCE,
    GESTURE_MAX_HANDS, FRAME_SKIP_RATE, GESTURE_WINDOW_SIZE,
    GESTURE_COMBO_REQUIRED, DOOR_OPEN_COOLDOWN, STREAM_LIFETIME
)
from utils.storage import get_screenshot_path
from utils.logger import logger_main, log_info, log_warning, log_error, log_door_open

# ---------- Глобальные переменные для обмена между циклом и сервером ----------

frame_times = deque()     
last_frame = None         
state_lock = threading.Lock()


def open_door(source_vebka=False, id_intercom=None):
    """
    Основной цикл обработки видеопотока
    
    Args:
        source_vebka: если True, использует веб-камеру вместо потока
        id_intercom: ID интеркома для получения потока
    """
    if id_intercom is None:
        id_intercom = INTERCOM_ID
    
    c = 0
    global last_frame

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=GESTURE_MAX_HANDS,
        min_detection_confidence=GESTURE_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=GESTURE_MIN_TRACKING_CONFIDENCE
    )

    log_info("door_open", f"Starting door opening service (intercom_id={id_intercom})")

    def get_session():
        task = Task(
            kind="get_website_session",
            data=None,
            need_result=True
        )
        task_queue.put(task)
        task.event.wait()
        log_info("door_open", "New session obtained")
        return task.result

    def get_stream_url(session, id_intercom):    
        data = {"session": session, "id_intercom": id_intercom}
        
        task = Task(
            kind="get_stream_url",
            data=data,
            need_result=True
        )
        task_queue.put(task)
        task.event.wait()
        return task.result
    
    def open_stream(session, id_intercom):
        stream_URL = get_stream_url(session, id_intercom)
        log_info("door_open", f"Stream URL: {stream_URL}")
        if not stream_URL:
            log_warning("door_open", "Can't get URL to stream")
            return None
        return cv2.VideoCapture(0 if source_vebka else stream_URL)
    
    findGesture = []
    last_open = time.time() - 10

    website_session = get_session()
    cap = open_stream(website_session, id_intercom)
    log_info(
        "door_open",
        f"opened={cap.isOpened()}"
    )
    stream_time_request = time.time() + STREAM_LIFETIME + random.randint(50, 120)

    ret, frame_bgr = None, None  
    log_info(
        "door_open",
        f"ret={ret}"
    )
    try:
        while True:
            now = datetime.now()            

            
            if time.time() > stream_time_request or not ret or frame_bgr is None:
                if cap:
                    log_info("door_open", "Requesting new stream URL...")
                    cap.release()
                    time.sleep(1)
                cap = open_stream(website_session, id_intercom)
                if not cap:
                    log_warning("door_open", "Can't open stream, requesting new session...")
                    website_session = get_session()
                    time.sleep(1)
                    continue
                stream_time_request = time.time() + STREAM_LIFETIME + random.randint(50, 120)

            ret, frame_bgr = cap.read()
            if not ret:
                log_warning("door_open", "cap.read() returned False")
                continue

            if frame_bgr is None:
                log_warning("door_open", "frame is None")
                continue
            # ==== обновляем статистику по кадрам ====
            t_now = time.time()
            with state_lock:
                frame_times.append(t_now)
                limit = t_now - 5.0
                while frame_times and frame_times[0] < limit:
                    frame_times.popleft()
                last_frame = frame_bgr.copy()
            
            c += 1
            if c % FRAME_SKIP_RATE == 0:
                continue

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            gesture_name = ""

            if results.multi_hand_landmarks and results.multi_handedness:
                for idx, (hand_landmarks, hand_handedness) in enumerate(
                    zip(results.multi_hand_landmarks, results.multi_handedness)
                ):
                    gesture_name = classify_gesture(hand_landmarks)

                    if gesture_name == "Hand too far":
                        continue
                    
                    task_queue.put(Task(
                        kind="db_insert_gesture",
                        data={"gesture": gesture_name}
                    ))

            findGesture.append(gesture_name)
            if len(findGesture) > GESTURE_WINDOW_SIZE:
                findGesture.pop(0)
                
                # Проверяем комбинацию жестов
                tidi_count = findGesture.count("TiDishi")
                rock_count = findGesture.count("Rock")
                
                if (tidi_count >= GESTURE_COMBO_REQUIRED.get("TiDishi", 5) and 
                    rock_count >= GESTURE_COMBO_REQUIRED.get("Rock", 2)):
                    
                    if time.time() - last_open > DOOR_OPEN_COOLDOWN:
                        last_open = time.time()

                        # Получаем путь с новой структурой (год/месяц/день)
                        gestures_used = ["TiDishi", "Rock"]
                        output_path = get_screenshot_path(now, gestures_used)

                        task_queue.put(Task(
                            kind="open_door",
                            data={
                                "token": BEARER_TOKEN,
                                "path": str(output_path),
                                "gestures": gestures_used
                            }
                        ))

                        task_queue.put(Task(
                            kind="save_screenshot",
                            data={"frame": last_frame, "path": str(output_path)}
                        ))
                        
                        log_door_open(str(output_path), gestures_used, 200, "Queued")

    except KeyboardInterrupt:
        log_info("door_open", "Stopping by Ctrl+C")
    except Exception as e:
        log_error("door_open", f"Unexpected error: {e}", exc_info=True)
    finally:
        hands.close()
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        log_info("door_open", "Shutdown complete")


# ===== ФУНКЦИИ ЗАПУСКА =====

def start_processing_thread():
    """Запускает поток обработки видео"""
    t = threading.Thread(target=open_door, kwargs={"source_vebka": False}, daemon=True)
    t.start()
    log_info("main", "Started processing thread")
    return t


if __name__ == "__main__":
    # Запускаем поток обработки видео (он работает независимо)
    log_info("main", "Starting OpenDoor service...")
    start_processing_thread()
    
    # Основной поток остаётся для других целей
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_info("main", "Shutdown signal received")
        import sys
        sys.exit(0)
