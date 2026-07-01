import requests
import urllib3
from django.conf import settings

urllib3.disable_warnings()


if not settings.PBX_VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PBXClient:
    def __init__(self):
        self.base_url = settings.PBX_BASE_URL
        self.verify_ssl = settings.PBX_VERIFY_SSL

    def authenticate(self):
        response = requests.post(
            f"{self.base_url}/authenticate",
            data={
                "user": settings.PBX_USER,
                "password": settings.PBX_PASSWORD,
            },
            timeout=15,
            verify=self.verify_ssl,
        )

        response.raise_for_status()
        data = response.json()

        return data.get("access_token")

    def get_cdr(self, token: str, params: dict | None = None):
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(
            f"{self.base_url}/cdr",
            headers=headers,
            params=params,
            timeout=15,
            verify=self.verify_ssl,
        )

        response.raise_for_status()
        return response.json()
