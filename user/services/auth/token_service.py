from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class UserTokenService:
    COOKIE_NAME = "refresh_token"
    COOKIE_MAX_AGE = 60 * 60 * 24 * 7

    COOKIE_SETTINGS = {
        "httponly": True,
        "secure": not settings.DEBUG,
        "samesite": "Strict",
        "max_age": COOKIE_MAX_AGE,
        "path": "/",
    }

    @staticmethod
    def get_tokens_for_user(user):
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    @staticmethod
    def get_tokens_for_user_from_refresh(refresh_token: str):
        try:
            refresh = RefreshToken(refresh_token)
            return str(refresh.access_token)
        except TokenError:
            raise TokenError("Invalid or expired refresh token")

    @classmethod
    def set_refresh_cookie(cls, response, refresh_token: str):
        response.set_cookie(
            key=cls.COOKIE_NAME,
            value=refresh_token,
            **cls.COOKIE_SETTINGS
        )
        return response

    @classmethod
    def clear_refresh_cookie(cls, response):
        response.delete_cookie(cls.COOKIE_NAME, path="/")
        return response
