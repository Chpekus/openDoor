import requests
import time
from dotenv import load_dotenv
import os
load_dotenv()
bearer_token = os.getenv("bearer_token")


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

