from rest_framework import serializers

from user.models import User
from user.services.user.user_service import UserService


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

    def validate_role(self, value):
        request = self.context.get('request')
        if request is None:
            return value
        actor = request.user
        if value == User.UserRoles.SUPERADMIN and not (
            actor.is_staff or actor.role == User.UserRoles.SUPERADMIN
        ):
            raise serializers.ValidationError("You are not allowed to assign this role.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request is not None and not request.user.is_staff:
            validated_data['organization'] = request.user.organization
        return UserService.create_user(validated_data)

    def update(self, instance, validated_data):
        return UserService.update_user(instance, validated_data)


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'full_name')
