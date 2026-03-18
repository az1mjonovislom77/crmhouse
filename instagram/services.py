import requests
from django.conf import settings


class InstagramAPIError(Exception):
    pass


class InstagramService:
    def __init__(self):
        self.base_url = f"{settings.GRAPH_BASE_URL}/{settings.INSTAGRAM_API_VERSION}"
        self.token = settings.INSTAGRAM_ACCESS_TOKEN

    def _request(self, method, endpoint, params=None, data=None):
        url = f"{self.base_url}/{endpoint}"

        params = params or {}
        params["access_token"] = self.token
        response = requests.request(method=method, url=url, params=params, json=data, timeout=10)

        if response.status_code != 200:
            raise InstagramAPIError(response.text)

        return response.json()

    def get_media(self, ig_user_id):
        return self._request("GET", f"{ig_user_id}/media", params={"fields": "id,caption"})

    def get_comments(self, media_id):
        return self._request("GET", f"{media_id}/comments", params={"fields": "id,text,username,timestamp"})

    def reply_to_comment(self, comment_id, message):
        return self._request("POST", f"{comment_id}/replies", data={"message": message})
