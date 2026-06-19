"""
Основное Flask приложение с вебинтерфейсом и API
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_session import Session
import os
from datetime import datetime, timedelta
from pathlib import Path
import cv2
import base64
from io import BytesIO

from config.settings import WEB_HOST, WEB_PORT, SECRET_KEY, INTERCOM_ID
from utils.auth import require_login, login_user, logout_user, verify_password, get_current_user, is_session_valid
from utils.storage import get_screenshot_path, get_day_screenshots, get_calendar_data, get_screenshot_info
from db.database import get_door_opens_for_day, get_recent_door_opens
from utils.logger import log_info, log_error

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# === АУТЕНТИФИКАЦИЯ ===

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if verify_password(username, password):
            login_user(username)
            return redirect(url_for('live'))
        else:
            return render_template('login.html', error='Неверное имя пользователя или пароль')
    
    if is_session_valid():
        return redirect(url_for('live'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Выход из системы"""
    logout_user()
    return redirect(url_for('login'))


# === ОСНОВНОЙ ИНТЕРФЕЙС ===

@app.route('/')
@require_login
def index():
    """Главная страница (редирект на live)"""
    return redirect(url_for('live'))


@app.route('/live')
@require_login
def live():
    """Страница просмотра текущего стрима"""
    username = get_current_user()
    log_info("app", f"User {username} viewing live stream")
    return render_template('live.html', username=username)


@app.route('/calendar')
@require_login
def calendar():
    """Страница календаря"""
    username = get_current_user()
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    # Получаем данные для календаря
    calendar_data = get_calendar_data(f"{year}", f"{month:02d}")
    
    log_info("app", f"User {username} viewing calendar {year}-{month}")
    
    return render_template(
        'calendar.html',
        username=username,
        year=year,
        month=month,
        calendar_data=calendar_data
    )


@app.route('/day/<year>/<month>/<day>')
@require_login
def day_view(year, month, day):
    """Страница просмотра дня с подробностями"""
    username = get_current_user()
    
    try:
        # Получаем скриншоты для дня из БД
        door_opens = get_door_opens_for_day(year, month, day)
        
        log_info("app", f"User {username} viewing day {year}-{month}-{day}")
        
        return render_template(
            'day.html',
            username=username,
            year=year,
            month=month,
            day=day,
            door_opens=door_opens
        )
    except Exception as e:
        log_error("app", f"Error viewing day: {e}")
        return render_template('error.html', message="Ошибка при загрузке дня"), 500


# === API ЭНДПОИНТЫ ===

@app.route('/api/stats')
@require_login
def api_stats():
    """API: Получить статистику обработки"""
    from core.analyzer import processed_frame_count, state_lock, stream_frame_count
    
    with state_lock:
        stream_frames = int(stream_frame_count)
        processed_frames = int(processed_frame_count)
    
    return jsonify({
        "stream_frames": stream_frames,
        "processed_frames": processed_frames,
        "server_time": datetime.now().isoformat()
    })


@app.route('/api/current_frame')
@require_login
def api_current_frame():
    """API: Получить текущий кадр из стрима"""
    try:
        from core.analyzer import processed_frame, state_lock
        
        with state_lock:
            if processed_frame is None:
                return jsonify({"error": "No frame available"}), 500
            frame_to_send = processed_frame.copy()
        
        # Конвертируем в JPEG
        ret, buffer = cv2.imencode('.jpg', frame_to_send)
        frame_bytes = buffer.tobytes()
        
        # Конвертируем в base64
        frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
        
        return jsonify({
            "frame": frame_base64,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        log_error("app", f"Error getting current frame: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/recent_opens')
@require_login
def api_recent_opens():
    """API: Получить недавние открытия двери"""
    limit = request.args.get('limit', 10, type=int)
    opens = get_recent_door_opens(limit)
    
    return jsonify({
        "opens": [
            {
                "timestamp": o['timestamp'].isoformat() if hasattr(o['timestamp'], 'isoformat') else str(o['timestamp']),
                "gestures": [],
                "response_code": o['response_code'],
                "img_path": o['img_path']
            }
            for o in opens
        ]
    })


@app.route('/api/image/<path:img_path>')
@require_login
def api_image(img_path):
    """API: Получить изображение скриншота"""
    try:
        requested_path = Path(img_path)
        full_path = requested_path if requested_path.is_absolute() else PROJECT_ROOT / requested_path
        full_path = full_path.resolve()
        if full_path.exists():
            mimetype = "video/webm" if full_path.suffix.lower() == ".webm" else "image/png"
            return send_file(full_path, mimetype=mimetype)
        else:
            return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        log_error("app", f"Error serving image: {e}")
        return jsonify({"error": str(e)}), 500


# === ОШИБКИ ===

@app.errorhandler(404)
def not_found(error):
    """Обработчик 404"""
    if is_session_valid():
        return render_template('error.html', message="Страница не найдена"), 404
    return redirect(url_for('login'))


@app.errorhandler(500)
def server_error(error):
    """Обработчик 500"""
    log_error("app", f"Server error: {error}")
    if is_session_valid():
        return render_template('error.html', message="Ошибка сервера"), 500
    return redirect(url_for('login'))
