import time

import requests
from django.conf import settings


class IssabelService:

    def __init__(self):
        self.access_token = None
        self.token_expires_at = 0

    def login(self):
        r = requests.post(
            f'{settings.ISSABEL_BASE_URL}/pbxapi/authenticate',
            data={
                'user': settings.ISSABEL_API_USER,
                'password': settings.ISSABEL_API_PASSWORD,
            },
            timeout=20,
            verify=False,
        )
        r.raise_for_status()
        data = r.json()
        self.access_token = data['access_token']
        self.token_expires_at = time.time() + data.get('expires_in', 3600) - 60

    def ensure_token(self):
        if not self.access_token or time.time() >= self.token_expires_at:
            self.login()

    def stream_recording(self, filename: str):
        self.ensure_token()
        r = requests.get(
            f'{settings.ISSABEL_BASE_URL}/pbxapi/recording',
            params={'filename': filename},
            headers={'Authorization': f'Bearer {self.access_token}'},
            stream=True,
            timeout=60,
            verify=False,
        )
        if r.status_code != 200:
            raise Exception(f'Recording fetch failed: {r.status_code}')
        return r
