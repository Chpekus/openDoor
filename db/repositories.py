"""Операции приложения с БД через SQLAlchemy ORM."""
from datetime import date, datetime, time

from sqlalchemy import select

from config.settings import SCREENSHOT_MAX_PER_DAY
from db.connection import session_scope
from db.models import DoorOpen, Gesture
from utils.logger import log_db_operation


def _door_open_dict(item):
    return {
        "img_path": item.img_path,
        "response_code": item.response_code,
        "response_text": item.response_text,
        "timestamp": item.timestamp,
    }


def insert_gesture(gesture_name):
    operation = "gesture.insert"
    started_at = datetime.now()
    try:
        with session_scope() as session:
            session.add(Gesture(gesture=gesture_name, timestamp=datetime.now()))
        log_db_operation(operation, True, (datetime.now() - started_at).total_seconds() * 1000)
    except Exception:
        log_db_operation(operation, False, (datetime.now() - started_at).total_seconds() * 1000)
        raise


def insert_door_open(img_path, response_code, response_text):
    operation = "door_open.insert"
    started_at = datetime.now()
    try:
        with session_scope() as session:
            session.add(DoorOpen(
                img_path=str(img_path),
                response_code=response_code,
                response_text=response_text,
                timestamp=datetime.now(),
            ))
        log_db_operation(operation, True, (datetime.now() - started_at).total_seconds() * 1000)
    except Exception:
        log_db_operation(operation, False, (datetime.now() - started_at).total_seconds() * 1000)
        raise


def get_door_opens_for_day(year, month, day):
    operation = "door_open.list_by_day"
    started_at = datetime.now()
    selected_day = date(int(year), int(month), int(day))
    start = datetime.combine(selected_day, time.min)
    end = datetime.combine(selected_day, time.max)

    try:
        with session_scope() as session:
            statement = (
                select(DoorOpen)
                .where(DoorOpen.timestamp >= start, DoorOpen.timestamp <= end)
                .order_by(DoorOpen.timestamp.desc())
                .limit(SCREENSHOT_MAX_PER_DAY)
                .execution_options(db_operation=operation)
            )
            result = [_door_open_dict(item) for item in session.scalars(statement).all()]
        log_db_operation(operation, True, (datetime.now() - started_at).total_seconds() * 1000)
        return result
    except Exception:
        log_db_operation(operation, False, (datetime.now() - started_at).total_seconds() * 1000)
        raise


def get_recent_door_opens(limit=10):
    operation = "door_open.list_recent"
    started_at = datetime.now()
    try:
        with session_scope() as session:
            statement = (
                select(DoorOpen)
                .order_by(DoorOpen.timestamp.desc())
                .limit(max(1, int(limit)))
                .execution_options(db_operation=operation)
            )
            result = [_door_open_dict(item) for item in session.scalars(statement).all()]
        log_db_operation(operation, True, (datetime.now() - started_at).total_seconds() * 1000)
        return result
    except Exception:
        log_db_operation(operation, False, (datetime.now() - started_at).total_seconds() * 1000)
        raise
