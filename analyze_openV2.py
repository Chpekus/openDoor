import recognition_alorithms
import novotelecom_integrarion

from dotenv import load_dotenv
import os
import time
from datetime import datetime
import math

import cv2
import csv
import numpy as np
import mediapipe as mp
import json
from collections import deque
import threading
from flask import Flask, jsonify

load_dotenv()
login = os.getenv("LOGIN")     
password = os.getenv("PASSWORD")
bearer_token = os.getenv("bearer_token")

# ---------- Глобальные переменные для обмена между циклом и сервером ----------

frame_times = deque()     
last_frame = None         
state_lock = threading.Lock() 

SCREENSHOTS_ROOT = "screenshots_test"
RESULTS_CSV = "gesture_results.csv"

app = Flask(__name__)


def open_door(source_vebka=False):
    c = 0
    global last_frame

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    findGesture = []
    last_open = 0

    os.makedirs(SCREENSHOTS_ROOT, exist_ok=True)

    csvfile = open(RESULTS_CSV, mode="w", newline="", encoding="utf-8")
    writer = csv.writer(csvfile, delimiter=";")
    writer.writerow(["timestamp", "filename", "hand_index", "handedness", "gesture"])

    def open_stream():
        stream_URL = novotelecom_integrarion.get_stream_url_via_requests(login, password)
        return cv2.VideoCapture(stream_URL)
        

    

    try:
        cap = open_stream()
        #print("Начинаю захват и анализ кадров...")

        while True:
            now = datetime.now()
            timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]
            

            ret, frame_bgr = cap.read()
            if not ret or frame_bgr is None:
                cap.release()
                time.sleep(1)
                cap = open_stream()
                continue
            

            # ==== обновляем статистику по кадрам ====
            t_now = time.time()
            with state_lock:
                frame_times.append(t_now)
                limit = t_now - 5.0
                while frame_times and frame_times[0] < limit:
                    frame_times.popleft()
                last_frame = frame_bgr.copy()
            
            c+=1 # Скип каждого второго кадра для т.к. сервак слабый и лень в оптимизацию пока
            if c%2==0:
                continue

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)
            output_frame = frame_bgr.copy()

            gesture_name = ""

            if results.multi_hand_landmarks and results.multi_handedness:
                for idx, (hand_landmarks, hand_handedness) in enumerate(
                    zip(results.multi_hand_landmarks, results.multi_handedness)
                ):
                    label = 0
                    gesture_name = recognition_alorithms.classify_gesture(hand_landmarks)

                    writer.writerow([
                        timestamp_str,
                        "",
                        idx,
                        label,
                        gesture_name
                    ])

            findGesture.append(gesture_name)
            if len(findGesture) > 20:
                findGesture.pop(0)
                if findGesture.count("TiDishi") >= 5 and findGesture.count("Rock") >= 2:
                    if time.time() - last_open > 7:
                        print(f"открытие двери в {now.strftime('%H-%M-%S')}")
                        novotelecom_integrarion.send_post_open_door_request(bearer_token)
                        last_open = time.time()

                        hour_dir = now.strftime("%H")
                        output_dir = os.path.join(SCREENSHOTS_ROOT, hour_dir)
                        os.makedirs(output_dir, exist_ok=True)

                        filename = f"{now.strftime('%H-%M-%S')}.png"
                        output_path = os.path.join(output_dir, filename)

                        cv2.imwrite(output_path, output_frame)

    except KeyboardInterrupt:
        print("Остановка по Ctrl+C")
    finally:
        hands.close()
        csvfile.close()
        cap.release()
        cv2.destroyAllWindows()
        print("Завершено.")


# ---------- HTTP-эндпоинты ----------

@app.route("/stats")
def stats():
    """
    Вернёт средний FPS за последние 5 секунд и количество кадров в этом окне.
    """
    with state_lock:
        if len(frame_times) < 2:
            fps = 0.0
            count = len(frame_times)
        else:
            dt = frame_times[-1] - frame_times[0]
            count = len(frame_times)
            fps = count / dt if dt > 0 else 0.0

    return jsonify({
        "fps_5s": round(fps, 2),
        "frames_in_window": count
    })


@app.route("/save_last_frame")
def save_last_frame():
    """
    Сохраняет последний обработанный кадр в файл и возвращает путь к нему.
    """
    with state_lock:
        if last_frame is None:
            return jsonify({"error": "Кадры ещё не были обработаны"}), 500
        frame_to_save = last_frame.copy()

    now = datetime.now()
    hour_dir = now.strftime("%H")
    output_dir = os.path.join(SCREENSHOTS_ROOT, "manual_saved", hour_dir)
    os.makedirs(output_dir, exist_ok=True)

    filename = f"manual_{now.strftime('%H-%M-%S')}.png"
    output_path = os.path.join(output_dir, filename)

    cv2.imwrite(output_path, frame_to_save)

    return jsonify({"saved_path": output_path})


def start_processing_thread():
    t = threading.Thread(target=open_door, kwargs={"source_vebka": False}, daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    # Запускаем поток обработки
    start_processing_thread()
    app.run(host="0.0.0.0", port=8000)

