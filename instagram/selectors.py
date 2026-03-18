from .services import InstagramService

instagram_service = InstagramService()


def fetch_comments(media_id):
    data = instagram_service.get_comments(media_id)
    return data.get("data", [])