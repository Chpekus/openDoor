import mediapipe as mp
import cv2
import os
import time

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
    


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

files = [os.path.join("data_test", f) for f in os.listdir("data_test") if f.endswith('.jpg') or f.endswith('.png')]

for _ in range(10):
    t = time.time()

    for file in files:
        image = cv2.imread(file)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)
        if results.multi_hand_landmarks and results.multi_handedness:
                # Найдены руки
                # gestures_for_filename = []

                for idx, (hand_landmarks, hand_handedness) in enumerate(
                    zip(results.multi_hand_landmarks, results.multi_handedness)
                ):
                    gesture_name = classify_gesture(hand_landmarks)
                    print(gesture_name, end='; ')

    print("Processed {} images in {:.2f} seconds, is {:.2f} per file".format(len(files), time.time() - t, (time.time() - t)/len(files)))
    
