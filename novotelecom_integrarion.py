import requests

def get_stream_url_via_requests(login = "", password = "", session = None):
    
    if session == None: # Будем создавать сессию при первой авторизации и использовать её при следющих запросах стрима
        session = requests.Session()

        login_url = "https://video.2090000.ru/login.html"
        payload = {
            "User[Login]": login,
            "User[Password]": password,
        }
        session.post(login_url, data=payload)

    url = "https://video.2090000.ru/account/camera/3104703/url.html" # Получаем ссылку на стрим камеры, пока по статичкому id домофона
    params = {
        "speed_mul": 1,
        "time": "",
        "timeZoneOffset": 25200,
        "format": "hls",
        "isSingleCamera": 1,
        "_": "",
    }

    resp = session.get(url, params=params)
    # session.close()
    # print(resp.status_code)
    # print(resp.json())
    return resp.json()['URL'], session # возвращаем ссылку на стрим и сессию


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
    print(resp.status_code)
    print(resp.text)
    return resp.status_code, resp.text