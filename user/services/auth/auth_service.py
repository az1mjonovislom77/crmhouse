from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from user.services.auth.rate_limit import check_login_rate_limit, reset_login_rate_limit
from user.services.auth.token_service import UserTokenService


class AuthService:

    @staticmethod
    def login_user(username, password, ip):
        if not check_login_rate_limit(ip, username):
            raise ValidationError({"detail": "Too many login attempts. Try again later"})

        user = authenticate(username=username, password=password)

        if not user or not user.is_active:
            raise ValidationError({"detail": "Invalid username or password."})

        tokens = UserTokenService.get_tokens_for_user(user)

        reset_login_rate_limit(ip, username)

        return {
            "user": user,
            "tokens": tokens
        }

    @staticmethod
    def refresh_user_token(refresh_token):
        if not refresh_token:
            raise ValidationError({"detail": "Refresh token not found"})

        try:
            access = UserTokenService.get_tokens_for_user_from_refresh(refresh_token)
            return {"access": access}
        except TokenError:
            raise ValidationError({"detail": "Invalid or expired refresh token."})

    @staticmethod
    def logout_user(refresh_token):
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            raise ValidationError({"detail": "Invalid or expired token."})
