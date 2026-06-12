"""
Слой работы с базой данных
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from config.settings import PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
from utils.logger import log_error, log_info


class Database:
    def __init__(self):
        self.conn = None
        self.connect()
    
    def connect(self):
        """Подключается к БД"""
        try:
            self.conn = psycopg2.connect(
                host=PGHOST,
                port=PGPORT,
                dbname=PGDATABASE,
                user=PGUSER,
                password=PGPASSWORD
            )
            self.conn.autocommit = True
            log_info("database", "Connected to PostgreSQL")
        except Exception as e:
            log_error("database", f"Failed to connect to PostgreSQL: {e}")
            self.conn = None
    
    def execute(self, sql, params=None):
        """Выполняет SQL запрос без результата"""
        if self.conn is None:
            self.connect()
        
        try:
            with self.conn.cursor() as cur:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                return cur.rowcount
        except Exception as e:
            log_error("database", f"Execute error: {e}\nSQL: {sql}")
            return 0
    
    def fetch_one(self, sql, params=None):
        """Получает одну строку результата"""
        if self.conn is None:
            self.connect()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                return cur.fetchone()
        except Exception as e:
            log_error("database", f"Fetch one error: {e}\nSQL: {sql}")
            return None
    
    def fetch_all(self, sql, params=None):
        """Получает все строки результата"""
        if self.conn is None:
            self.connect()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                return cur.fetchall()
        except Exception as e:
            log_error("database", f"Fetch all error: {e}\nSQL: {sql}")
            return []
    
    def close(self):
        """Закрывает подключение"""
        if self.conn:
            self.conn.close()
            log_info("database", "Connection closed")


def insert_gesture(gesture_name):
    """Вставляет найденный жест в БД"""
    db = Database()
    sql = "INSERT INTO find_gesture(gesture) VALUES (%s)"
    db.execute(sql, (gesture_name,))
    db.close()


def insert_door_open(img_path, response_code, response_text, gestures_used):
    """Вставляет запись об открытии двери"""
    db = Database()
    sql = """
        INSERT INTO case_of_open(img_path, response_code, response_text, gestures_used, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """
    db.execute(sql, (str(img_path), response_code, response_text, ",".join(gestures_used), datetime.now()))
    db.close()


def get_door_opens_for_day(year, month, day):
    """Получает все открытия двери за день"""
    db = Database()
    sql = """
        SELECT img_path, response_code, response_text, gestures_used, timestamp
        FROM case_of_open
        WHERE DATE(timestamp) = %s
        ORDER BY timestamp DESC
        LIMIT %s
    """
    date_str = f"{year}-{month}-{day}"
    from config.settings import SCREENSHOT_MAX_PER_DAY
    result = db.fetch_all(sql, (date_str, SCREENSHOT_MAX_PER_DAY))
    db.close()
    return result or []


def get_recent_door_opens(limit=10):
    """Получает последние открытия двери"""
    db = Database()
    sql = """
        SELECT img_path, response_code, response_text, gestures_used, timestamp
        FROM case_of_open
        ORDER BY timestamp DESC
        LIMIT %s
    """
    result = db.fetch_all(sql, (limit,))
    db.close()
    return result or []
