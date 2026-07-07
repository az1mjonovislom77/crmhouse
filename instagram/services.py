import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class InstagramAPIError(Exception):
    pass


class InstagramService:
    def __init__(self):
        self.base_url = f"{settings.GRAPH_BASE_URL}/{settings.INSTAGRAM_API_VERSION}"
        self.token = settings.INSTAGRAM_ACCESS_TOKEN

    def _request(self, method, endpoint, params=None, data=None):
        url = f"{self.base_url}/{endpoint}"

        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.request(method=method, url=url, params=params, json=data,
                                    headers=headers, timeout=10)

        if response.status_code != 200:
            logger.error("Instagram API xatosi [%s %s]: %s", method, endpoint, response.text)
            raise InstagramAPIError("Instagram API bilan ishlashda xato yuz berdi")

        return response.json()

    def get_media(self, ig_user_id):
        return self._request("GET", f"{ig_user_id}/media", params={"fields": "id,caption"})

    def get_comments(self, media_id):
        return self._request("GET", f"{media_id}/comments", params={"fields": "id,text,username,timestamp"})

    def reply_to_comment(self, comment_id, message):
        return self._request("POST", f"{comment_id}/replies", data={"message": message})
