"""ORM-модели существующих таблиц PostgreSQL."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Gesture(Base):
    __tablename__ = "find_gesture"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gesture: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DoorOpen(Base):
    __tablename__ = "case_of_open"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    img_path: Mapped[str] = mapped_column(String(500), nullable=False)
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    gestures_used: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
