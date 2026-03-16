from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class AuthService:

    @staticmethod
    def authenticate_user(username, password):
        user = authenticate(username=username, password=password)

        if not user or not user.is_active:
            raise ValidationError("Invalid username or password.")

        return user

    @staticmethod
    def logout_user(refresh_token):
        try:
            RefreshToken(refresh_token).blacklist()
            return True
        except TokenError:
            raise ValidationError("Invalid or expired token.")
