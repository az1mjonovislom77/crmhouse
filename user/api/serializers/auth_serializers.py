from user.models import User
from rest_framework import serializers


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if not attrs.get("username") or not attrs.get("password"):
            raise serializers.ValidationError("Username and password required")
        return attrs


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name", "username", "phone_number", "role", "is_active")
