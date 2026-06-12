"""
Интеграция с API Новотелеком
"""
import requests
import os
from dotenv import load_dotenv
from requests.exceptions import RequestException
import json
from utils.logger import log_error, log_info, log_warning

load_dotenv()
login = os.getenv("LOGIN")     
password = os.getenv("PASSWORD")


def make_session():
    """Создает сеанс на сайте новотелекома с камерами домофонов по логину, паролю из env"""
    session = requests.Session()
    login_url = "https://video.2090000.ru/login.html"
    payload = {
        "User[Login]": login,
        "User[Password]": password,
    }
    try:
        response = session.post(login_url, data=payload)
        log_info("novotelecom", f"Session created, status: {response.status_code}")
        return session
    except Exception as e:
        log_error("novotelecom", f"Failed to create session: {e}")
        return None


def get_stream_url(session, id_intercom=0):
    """Получает ссылку на стрим камеры по ID домофона"""
    if not session:
        log_warning("novotelecom", "Session is not provided")
        return None
    
    if id_intercom == 0:
        log_warning("novotelecom", "Undefined id intercom")
        return None
    
    url = f"https://video.2090000.ru/account/camera/{id_intercom}/url.html"
    
    params = {
        "speed_mul": 1,
        "time": "",
        "timeZoneOffset": 25200,
        "format": "hls",
        "isSingleCamera": 1,
        "_": "",
    }
    try:
        resp = session.get(url, params=params)
        if resp.status_code != 200:
            log_error("novotelecom", f"Bad status: {resp.status_code}, url: {resp.url}")
            return None
        
        data = resp.json()
        stream_url = data.get("URL")
        if not stream_url:
            log_warning("novotelecom", f"No URL field in response. Keys: {list(data.keys())}")
            return None

        log_info("novotelecom", f"Stream URL obtained for intercom {id_intercom}")
        return stream_url

    except json.JSONDecodeError as e:
        log_error("novotelecom", f"JSON decode failed: {e}")
        return None
    except RequestException as e:
        log_error("novotelecom", f"Request failed: {e}")
        return None


def send_post_open_door_request(bearer_token):
    """Отправляет запрос на открытие двери"""
    url = "https://myhome.proptech.ru/rest/v1/places/260209/accesscontrols/10586/entrances/1824/actions"

    headers = {
        "user-agent": "samsung SMS908E | Android 9 | ntkSmartphoneGmsGooglePlay | 6.21.0 (7040302) | 65973 | 1 | 1da05087-058e-40a4-918b-e1a6675674b2",
        "operator": "1",
        "authorization": f"Bearer {bearer_token}",
        "content-type": "application/json; charset=UTF-8",
        "content-length": "28",
        "accept-encoding": "gzip"
    }

    payload = {
        "name": "accessControlOpen"
    }

    try:
        resp = requests.post(url, json=payload, headers=headers)
        log_info("novotelecom", f"Door open request sent, status: {resp.status_code}")
        return resp.status_code, resp.text
    except Exception as e:
        log_error("novotelecom", f"Failed to send door open request: {e}")
        return 500, str(e)
