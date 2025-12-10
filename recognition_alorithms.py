import math

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

    maxDist = 0
    for tips_id in finger_tips:
        dist = math.sqrt((hand_landmarks.landmark[0].x - hand_landmarks.landmark[tips_id].x)**2 + (hand_landmarks.landmark[0].y - hand_landmarks.landmark[tips_id].y)**2)
        if dist > maxDist:
            maxDist = dist

    if maxDist > 0.3:
        for tip_id, pip_id, coeff_id in zip(finger_tips, finger_pips, coeffForFingers):
            open_finger.append(finger_is_open(hand_landmarks.landmark[0], hand_landmarks.landmark[tip_id], hand_landmarks.landmark[pip_id], coeff_id))

        return open_finger
    else:
        return -1


def classify_gesture(hand_landmarks):
    """
    Классификация жеста по количеству открытых пальцев и их относительному расположению.
    """
    list_open_fingers = open_fingers(hand_landmarks)
    #return f"{list_open_fingers}"
    if list_open_fingers == -1:
        return "Hand too far"
    
    count_open_fingers = sum(list_open_fingers)
    
    if count_open_fingers == 0:
        return "Fist"
    elif count_open_fingers == 5:
        return "Open Hand"
    elif count_open_fingers == 1 and list_open_fingers[1] == 1:
        return "Ukazannie"
    elif count_open_fingers == 2 and list_open_fingers[1] == 1 and list_open_fingers[2] == 1: 
        return "Victory"
    elif count_open_fingers == 3 and list_open_fingers[0] == 1 and list_open_fingers[1] == 1 and list_open_fingers[2] == 1: 
        return "TiDishi"
    elif count_open_fingers == 2 and list_open_fingers[0] == 1 and list_open_fingers[4] == 1: 
        return "Jambo"
    elif count_open_fingers == 3 and list_open_fingers[0] == 1 and list_open_fingers[1] == 1 and list_open_fingers[4] == 1: 
        return "Rock"
    else:
        return f"{list_open_fingers}: {count_open_fingers}"