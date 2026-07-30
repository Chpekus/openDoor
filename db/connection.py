"""SQLAlchemy engine и пул ORM-сессий."""
from contextlib import contextmanager
from queue import Queue
from threading import Lock
from time import perf_counter

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from config.settings import (
    DEBUG,
    DB_SESSION_POOL_SIZE,
    PGDATABASE,
    PGHOST,
    PGPASSWORD,
    PGPORT,
    PGUSER,
)
from utils.logger import log_db_operation


DATABASE_URL = (
    f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}"
    f"@{PGHOST}:{PGPORT}/{PGDATABASE}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._db_started_at = perf_counter()


def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    duration_ms = (perf_counter() - context._db_started_at) * 1000
    log_db_operation(
        operation=context.execution_options.get("db_operation", "sqlalchemy.execute"),
        success=True,
        duration_ms=duration_ms,
        statement=statement,
        params=parameters,
        debug=DEBUG,
    )


def _handle_db_error(exception_context):
    context = exception_context.execution_context
    started_at = getattr(context, "_db_started_at", perf_counter())
    duration_ms = (perf_counter() - started_at) * 1000
    log_db_operation(
        operation=context.execution_options.get("db_operation", "sqlalchemy.execute"),
        success=False,
        duration_ms=duration_ms,
        statement=exception_context.statement,
        params=exception_context.parameters,
        debug=DEBUG,
    )


event.listen(engine, "before_cursor_execute", _before_cursor_execute)
event.listen(engine, "after_cursor_execute", _after_cursor_execute)
event.listen(engine, "handle_error", _handle_db_error)


class SessionPool:
    """Пул переиспользуемых Session, выдаваемых только одному потоку за раз."""

    def __init__(self, size=DB_SESSION_POOL_SIZE):
        if size < 1:
            raise ValueError("Session pool size must be positive")
        self._sessions = Queue(maxsize=size)
        self._all_sessions = []
        self._lock = Lock()
        for _ in range(size):
            session = SessionFactory()
            self._sessions.put(session)
            self._all_sessions.append(session)

    @contextmanager
    def acquire(self):
        session = self._sessions.get()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.expunge_all()
            session.close()
            self._sessions.put(session)

    def close(self):
        with self._lock:
            while self._all_sessions:
                self._all_sessions.pop().close()


session_pool = SessionPool()


@contextmanager
def session_scope():
    """Выдаёт сессию приложению или worker и завершает транзакцию."""
    with session_pool.acquire() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
