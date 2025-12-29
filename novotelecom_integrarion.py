import requests
import os
from dotenv import load_dotenv

load_dotenv()
login = os.getenv("LOGIN")     
password = os.getenv("PASSWORD")

def make_session():
        session = requests.Session() # Создаем сессию на сайте новотелекома с камерами домофонов по логину, паролю из env
        login_url = "https://video.2090000.ru/login.html"
        payload = {
            "User[Login]": login,
            "User[Password]": password,
        }
        session.post(login_url, data=payload)
        return session

def get_stream_url(session = None, id_intercom = 0):
    
    if session == None: # Будем создавать сессию при первой авторизации и использовать её при следющих запросах стрима
        session = make_session()

    url = f"https://video.2090000.ru/account/camera/{id_intercom}/url.html" # Получаем ссылку на стрим камеры, по  id домофона
    
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
        URL_Stream = resp.json()['URL']
    except Exception as e:
        print(URL_Stream)
        print(f"Error in novotelecom integration {e}")
        return 0
    
    return URL_Stream, session

def send_post_open_door_request(bearer_token):
    url = "https://myhome.proptech.ru/rest/v1/places/260209/accesscontrols/10586/entrances/1824/actions"

    headers = {
        "user-agent":       "samsung SMS908E | Android 9 | ntkSmartphoneGmsGooglePlay | 6.21.0 (7040302) | 65973 | 1 | 1da05087-058e-40a4-918b-e1a6675674b2",
        "operator":         "1",
        "authorization":    f"Bearer {bearer_token}", # Ключ получен в пятницу 5.12.2025
        "content-type":    "application/json; charset=UTF-8",
        "content-length":   "28",
        "accept-encoding":  "gzip"
    }

    payload = {
        "name": "accessControlOpen"
    }

    resp = requests.post(url, json=payload, headers=headers)

    return resp.status_code, resp.text