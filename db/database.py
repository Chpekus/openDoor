"""Совместимый фасад над ORM-репозиториями.

Новый код должен импортировать операции из ``db.repositories`` напрямую.
"""
from db.repositories import (
    get_door_opens_for_day,
    get_recent_door_opens,
    insert_door_open,
    insert_gesture,
)

__all__ = [
    "get_door_opens_for_day",
    "get_recent_door_opens",
    "insert_door_open",
    "insert_gesture",
]
