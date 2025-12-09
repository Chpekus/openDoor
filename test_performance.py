import mediapipe as mp
import cv2
import os
import time
from multiprocessing import Pool, cpu_count

def finger_is_open(wrist, tip, pip, coeff):
    """
    Считаем палец "открытым", расстояние от кисти до кончика пальца больше, 
    чем (расстояние от кисти до первой фаланги пальца) * 1.45.
    """


    def powDist(a, b):
        return ((a.x - b.x)*(a.x - b.x) + (a.y - b.y)*(a.y - b.y))
    #return [int(powDist(wrist, pip) * coeff*coeff < powDist(wrist, tip)), str(powDist(wrist, pip) * coeff*coeff)[:4], str(powDist(wrist, tip))[:4]]
    #print(powDist(wrist, pip) * coeff*coeff, powDist(wrist, tip))
    return int(powDist(wrist, pip) * coeff*coeff < powDist(wrist, tip))


def open_fingers(hand_landmarks):
    """
    Возвращает количество "открытых" пальцев для одной руки.
    """
    finger_tips = [4, 8, 12, 16, 20]
    finger_pips = [2, 5, 9, 13, 17]
    coeffForFingers = [1.5, 1.6, 1.8, 1.8, 1.6]

    open_finger = []
    
    for tip_id, pip_id, coeff_id in zip(finger_tips, finger_pips, coeffForFingers):
        open_finger.append(finger_is_open(hand_landmarks.landmark[0], hand_landmarks.landmark[tip_id], hand_landmarks.landmark[pip_id], coeff_id))

    return open_finger


def classify_gesture(hand_landmarks):
    """
    Классификация жеста по количеству открытых пальцев и их относительному расположению.
    """
    list_open_fingers = open_fingers(hand_landmarks)
    #return f"{list_open_fingers}"

    count_open_fingers = sum(list_open_fingers)
    
    if count_open_fingers == 0:
        return f"Fist"
    elif count_open_fingers == 5:
        return f"Open Hand"
    elif count_open_fingers == 1 and list_open_fingers[1] == 1:
        return f"Ukazannie"
    elif count_open_fingers == 2 and list_open_fingers[1] == 1 and list_open_fingers[2] == 1: 
        return f"Victory"
    elif count_open_fingers == 3 and list_open_fingers[0] == 1 and list_open_fingers[1] == 1 and list_open_fingers[2] == 1: 
        return f"TiDishi"
    elif count_open_fingers == 2 and list_open_fingers[0] == 1 and list_open_fingers[4] == 1: 
        return f"Jambo"
    elif count_open_fingers == 3 and list_open_fingers[0] == 1 and list_open_fingers[1] == 1 and list_open_fingers[4] == 1: 
        return f"Rock"
    else:
        return f"{list_open_fingers}: {count_open_fingers}"
    
# Глобальные для КАЖДОГО процесса (в main-процессе они не используются)
mp_hands = None
hands = None

def init_worker():
    """
    Вызывается один раз при старте КАЖДОГО процесса пула.
    Здесь создаём свой экземпляр Hands.
    """
    global mp_hands, hands
    import mediapipe as mp  # импорт внутри, чтобы корректно работать в дочернем процессе

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )

def process_file(file_path):
    """
    Обрабатывает ОДИН файл: читает, прогоняет через mediapipe, классифицирует жесты.
    Возвращает, например, (имя_файла, список_жестов).
    """
    global hands

    image = cv2.imread(file_path)
    if image is None:
        return file_path, []  # файл не прочитался

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    gestures = []

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, hand_handedness in zip(
            results.multi_hand_landmarks, results.multi_handedness
        ):
            gesture_name = classify_gesture(hand_landmarks)
            gestures.append(gesture_name)

    return file_path, gestures


if __name__ == "__main__":
    # список файлов
    files = [
        os.path.join("data_test", f)
        for f in os.listdir("data_test")
        if f.endswith('.jpg') or f.endswith('.png')
    ]

    num_workers = int(input("Введите количество воркеров для теста: "))

    avg_times = 0
    count_test = int(input("Введите количество прогонов для теста: "))
    for _ in range(count_test):
        

        with Pool(processes=num_workers, initializer=init_worker) as pool:
            # imap_unordered даёт результаты по мере готовности
            t_start = 0
            c = 0
            for file_path, gestures in pool.imap_unordered(process_file, files):
                if t_start == 0:
                    t_start = time.time()
                c+= 1
                # если хочешь печатать —
                if gestures:
                    print(os.path.basename(file_path), "->", "; ".join(gestures))
                # если не нужно печатать — можешь убрать это для ещё большей скорости

        elapsed = time.time() - t_start
        print(
            "Processed {} images in {:.2f} seconds, is {:.4f} per file ({} workers; {} find gest)".format(
                len(files), elapsed, elapsed / len(files), num_workers, c
            )
        )
        avg_times += elapsed / len(files)
print("Average time per file over {} runs: {:.4f} seconds with {} workers".format(count_test, avg_times / count_test, num_workers))