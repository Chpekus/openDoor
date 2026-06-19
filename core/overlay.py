import cv2


LOCKED = "locked"
PENDING = "pending"
OPEN = "open"
ERROR = "error"

WHITE = (245, 245, 245)
SHADOW = (20, 20, 20)
LABEL_PADDING = 6
LABEL_GAP = 10


def draw_lock_status(frame, state=LOCKED, origin=(18, 18)):
    x, y = origin
    body_w, body_h = 30, 24
    shackle_w, shackle_h = 20, 20
    body_x = x
    body_y = y + 18

    color = _status_color(state)

    cv2.rectangle(
        frame,
        (body_x + 2, body_y + 2),
        (body_x + body_w + 2, body_y + body_h + 2),
        SHADOW,
        thickness=-1,
    )
    cv2.rectangle(
        frame,
        (body_x, body_y),
        (body_x + body_w, body_y + body_h),
        color,
        thickness=2,
    )

    if state == OPEN:
        _draw_open_shackle(frame, body_x, body_y, shackle_w, shackle_h, color)
    else:
        _draw_closed_shackle(frame, body_x, body_y, shackle_w, shackle_h, color)

    cv2.circle(frame, (body_x + body_w // 2, body_y + 12), 3, color, thickness=-1)

    if state == PENDING:
        cv2.circle(frame, (body_x + body_w + 8, body_y + 3), 3, WHITE, thickness=-1)
    elif state == ERROR:
        cv2.line(frame, (body_x + 9, body_y + 8), (body_x + 21, body_y + 20), WHITE, 2)
        cv2.line(frame, (body_x + 21, body_y + 8), (body_x + 9, body_y + 20), WHITE, 2)


def draw_hand_landmarks(frame, hand_landmarks, mp_hands, mp_drawing):
    mp_drawing.draw_landmarks(
        frame,
        hand_landmarks,
        mp_hands.HAND_CONNECTIONS,
    )


def draw_gesture_label(frame, hand_landmarks, gesture_name):
    if not gesture_name:
        return

    frame_h, frame_w = frame.shape[:2]
    points = [
        (int(landmark.x * frame_w), int(landmark.y * frame_h))
        for landmark in hand_landmarks.landmark
    ]
    if not points:
        return

    anchor_x, anchor_y = max(points, key=lambda point: point[1])
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.65
    thickness = 2
    text_size, baseline = cv2.getTextSize(gesture_name, font, font_scale, thickness)
    text_w, text_h = text_size
    box_w = text_w + LABEL_PADDING * 2
    box_h = text_h + baseline + LABEL_PADDING * 2

    x = anchor_x + LABEL_GAP
    if x + box_w > frame_w:
        x = anchor_x - LABEL_GAP - box_w

    x = max(0, min(x, frame_w - box_w))
    y = anchor_y + LABEL_GAP
    if y + box_h > frame_h:
        y = anchor_y - LABEL_GAP - box_h

    y = max(0, min(y, frame_h - box_h))

    cv2.rectangle(
        frame,
        (x + 2, y + 2),
        (x + box_w + 2, y + box_h + 2),
        SHADOW,
        thickness=-1,
    )
    cv2.rectangle(
        frame,
        (x, y),
        (x + box_w, y + box_h),
        SHADOW,
        thickness=-1,
    )
    cv2.putText(
        frame,
        gesture_name,
        (x + LABEL_PADDING, y + LABEL_PADDING + text_h),
        font,
        font_scale,
        WHITE,
        thickness,
        cv2.LINE_AA,
    )


def _draw_closed_shackle(frame, body_x, body_y, shackle_w, shackle_h, color):
    shackle_x = body_x + (30 - shackle_w) // 2
    cv2.ellipse(
        frame,
        (shackle_x + shackle_w // 2, body_y),
        (shackle_w // 2, shackle_h // 2),
        180,
        0,
        180,
        color,
        thickness=3,
    )
    cv2.line(frame, (shackle_x, body_y), (shackle_x, body_y + 8), color, 3)
    cv2.line(
        frame,
        (shackle_x + shackle_w, body_y),
        (shackle_x + shackle_w, body_y + 8),
        color,
        3,
    )


def _draw_open_shackle(frame, body_x, body_y, shackle_w, shackle_h, color):
    shackle_x = body_x + (30 - shackle_w) // 2
    cv2.ellipse(
        frame,
        (shackle_x + shackle_w // 2 + 7, body_y - 1),
        (shackle_w // 2, shackle_h // 2),
        215,
        0,
        170,
        color,
        thickness=3,
    )
    cv2.line(
        frame,
        (shackle_x + shackle_w + 4, body_y + 1),
        (shackle_x + shackle_w + 4, body_y + 9),
        color,
        3,
    )


def _status_color(state):
    return WHITE
