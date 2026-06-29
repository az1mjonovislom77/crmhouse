from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class UserTokenService:
    COOKIE_NAME = "refresh_token"
    COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

    COOKIE_SETTINGS = {
        "httponly": True,
        "secure": not settings.DEBUG,
        "samesite": "Lax" if settings.DEBUG else "None",
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
    def rotate_refresh_token(refresh_token_str: str):
        """Eski tokenni blacklist qiladi, yangi access+refresh qaytaradi."""
        try:
            refresh = RefreshToken(refresh_token_str)
            new_access = str(refresh.access_token)
            refresh.blacklist()
            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()
            return {"access": new_access, "refresh": str(refresh)}
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
        response.delete_cookie(
            cls.COOKIE_NAME,
            path="/",
            samesite=cls.COOKIE_SETTINGS["samesite"],
        )
        return response
