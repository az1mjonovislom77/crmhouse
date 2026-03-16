from user.models import User
from rest_framework import serializers
from user.services.user_service import UserService


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "username", "phone_number", "role", "is_active"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'username', 'phone_number', 'password', 'role']
        read_only_fields = ['id']

    def create(self, validated_data):
        return UserService.create_user(validated_data)

    def update(self, instance, validated_data):
        return UserService.update_user(instance, validated_data)
