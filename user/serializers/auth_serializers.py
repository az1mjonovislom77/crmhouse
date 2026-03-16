from user.models import User
from rest_framework import serializers
from user.services.auth_service import AuthService


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = AuthService.authenticate_user(username=attrs.get("username"), password=attrs.get("password"))

        if not user:
            raise serializers.ValidationError("Invalid username or password")

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self, **kwargs):
        AuthService.logout_user(self.validated_data["refresh"])
        return self.validated_data


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name", "username", "phone_number", "role", "is_active")
