import cv2


LOCKED = "locked"
PENDING = "pending"
OPEN = "open"
ERROR = "error"

WHITE = (245, 245, 245)
SHADOW = (20, 20, 20)


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
