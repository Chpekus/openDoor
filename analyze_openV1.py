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

load_dotenv()
login = os.getenv("LOGIN"), 
password = os.getenv("PASSWORD")
bearer_token = os.getenv("bearer_token")





def open_door(source_vebka = False):

    global current_fps
    # ==== MediaPipe и жесты ====
    mp_hands = mp.solutions.hands
    # mp_drawing = mp.solutions.drawing_utils
    # Инициализируем MediaPipe Hands (для видео лучше static_image_mode=False)
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    SCREENSHOTS_ROOT = "screenshots_test"   # корневая папка для сохранения
    RESULTS_CSV = "gesture_results.csv"
   
    # ==== MediaPipe и жесты ====

    findGesture = []
    first_time = time.time()
    times = []
    current_fps = 0
    last_open = 0


    # ==== Selenium: запускаем браузер ====

    # Открываем CSV заранее
    csvfile = open(RESULTS_CSV, mode="w", newline="", encoding="utf-8")
    writer = csv.writer(csvfile, delimiter=";")
    writer.writerow(["timestamp", "filename", "hand_index", "handedness", "gesture"])


    try:
        if not(source_vebka):
            stream_URL = novotelecom_integrarion.get_stream_url_via_requests(login, password)
            #stream_URL = get_stream_url_via_selenium()
            cap = cv2.VideoCapture(stream_URL)
        else:
            cap = cv2.VideoCapture(0)
        
        print("Начинаю захват и анализ кадров... (Ctrl+C чтобы остановить)")

        while True:
            now = datetime.now()
            # Для имени файла и логов
            timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]  # до миллисекунд

            # Делаем скриншот элемента <video> в PNG (байты)
            ret, frame_bgr = cap.read()
            if not ret or frame_bgr is None:
                print("Не удалось прочитать кадр с веб-камеры, пропускаю кадр")
                continue

            # BGR -> RGB для MediaPipe
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            # Анализ руками
            results = hands.process(frame_rgb)

            # Будем рисовать на копии исходного кадра
            output_frame = frame_bgr.copy()

            times.append(round(time.time() - first_time, 2))
            if len(times) > 20:
                times.pop(0)
                print(f"Средний FPS: {(20/(times[-1] - times[0])):.2f}")

            
            gesture_name = ""

            if results.multi_hand_landmarks and results.multi_handedness:
                # Найдены руки
                # gestures_for_filename = []

                for idx, (hand_landmarks, hand_handedness) in enumerate(
                    zip(results.multi_hand_landmarks, results.multi_handedness)
                ):
                    #label = hand_handedness.classification[0].label  # "Left" / "Right"
                    label = 0
                    # gesture_name = classify_gesture(hand_landmarks, label)
                    gesture_name = recognition_alorithms.classify_gesture(hand_landmarks)
                    
                    # gestures_for_filename.append(f"{label}_{gesture_name}")

                    # Рисуем скелет руки
                    # mp_drawing.draw_landmarks(
                    #     output_frame,
                    #     hand_landmarks,
                    #     mp_hands.HAND_CONNECTIONS
                    # )

                    # Подпишем жест около запястья
                    # h, w, _ = output_frame.shape
                    # wrist = hand_landmarks.landmark[0]
                    # x = int(wrist.x * w)
                    # y = int(wrist.y * h)

                    # cv2.putText(
                    #     output_frame,
                    #     f"{label}: {gesture_name}",
                    #     (x, max(20, y - 10)),
                    #     cv2.FONT_HERSHEY_SIMPLEX,
                    #     0.7,
                    #     (0, 255, 0),
                    #     2
                    # )

                    # Запись в CSV
                    writer.writerow([
                        timestamp_str,
                        "",            # имя файла подставим позже, если сохраним
                        idx,
                        label,
                        gesture_name
                    ])

                # Если хотя бы одна рука найдена — сохраняем кадр

            findGesture.append(gesture_name)
            # current_stats['gesture'] = (findGesture)
            if len(findGesture) > 20:
                findGesture.pop(0)
                if findGesture.count("TiDishi") >= 5 and findGesture.count("Rock") >= 2:
                    #gesture_str = "-".join(gestures_for_filename)
                    
                    if time.time() - last_open > 7: # Интервал между нажатиями должен быть больше 7 секунд
                        print(f"откртыие двери в {now.strftime('%H-%M-%S')}")
                        novotelecom_integrarion.send_post_open_door_request(bearer_token)
                        # tap(300, 616) # Открытие двери с помощью тапа по экрану
                        last_open = time.time()
                        # current_stats["open_time"] = last_open
                    # Структура папок: screenshots/HH/MM/
                    hour_dir = now.strftime("%H")
                    output_dir = os.path.join(SCREENSHOTS_ROOT, hour_dir)
                    os.makedirs(output_dir, exist_ok=True)

                    filename = f"{now.strftime('%H-%M-%S')}.png"
                    output_path = os.path.join(output_dir, filename)

                    cv2.imwrite(output_path, output_frame)
                    # print(f"[{timestamp_str}] Найдены жесты: {gesture_str} -> {output_path}")
                        

                # Дописываем имя файла в последнюю строку CSV (если нужно прямо связать)
                # Проще: можно сразу писать filename в writer.writerow выше,
                # тут для простоты оставим как есть.

            # ret, buffer = cv2.imencode('.jpg', output_frame)
            # if not ret:
            #     continue
            # frame = buffer.tobytes()

            # # MJPEG-ответ: каждый кадр — отдельная часть multipart-потока
            
            # yield (b'--frame\r\n'
            #         b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            #time.sleep(FRAME_INTERVAL)

    except KeyboardInterrupt:
        print("Остановка по Ctrl+C")

    finally:
        hands.close()
        csvfile.close()
        cap.release()
        cv2.destroyAllWindows()
        print("Завершено.")

if __name__ == "__main__":
    open_door(source_vebka = False)