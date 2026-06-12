"""
Логика аутентификации и управления сеансами
"""
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for
from config.settings import USERS, SECRET_KEY
from utils.logger import log_info, log_warning

SESSION_TIMEOUT = 24  # часов


def hash_password(password):
    """Хеширует пароль"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(username, password):
    """Проверяет правильность пароля"""
    if username not in USERS:
        log_warning("auth", f"Login attempt with non-existent user: {username}")
        return False
    
    stored_password = USERS[username]
    
    # Сравниваем напрямую (в реальном приложении должно быть хешированием)
    if password == stored_password:
        log_info("auth", f"Successful login: {username}")
        return True
    
    log_warning("auth", f"Failed login attempt: {username}")
    return False


def login_user(username):
    """Создаёт сеанс для пользователя"""
    session['username'] = username
    session['login_time'] = datetime.now().isoformat()
    session['last_activity'] = datetime.now().isoformat()
    log_info("auth", f"Session created for: {username}")


def logout_user():
    """Завершает сеанс"""
    username = session.get('username', 'Unknown')
    session.clear()
    log_info("auth", f"Session closed for: {username}")


def is_session_valid():
    """Проверяет, валиден ли текущий сеанс"""
    if 'username' not in session:
        return False
    
    try:
        login_time = datetime.fromisoformat(session.get('login_time', ''))
        if datetime.now() - login_time > timedelta(hours=SESSION_TIMEOUT):
            log_warning("auth", f"Session expired for: {session.get('username')}")
            return False
        
        # Обновляем время активности
        session['last_activity'] = datetime.now().isoformat()
        return True
    except:
        return False


def require_login(f):
    """Декоратор для защиты эндпоинтов, требующих авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_session_valid():
            log_warning("auth", "Access attempt without valid session")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Возвращает имя текущего пользователя или None"""
    if is_session_valid():
        return session.get('username')
    return None
