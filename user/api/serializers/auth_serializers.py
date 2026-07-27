from rest_framework import serializers

from user.models import User


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if not attrs.get("username") or not attrs.get("password"):
            raise serializers.ValidationError("Username and password required")
        return attrs


class MeSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(read_only=True, source="organization.name")
    organization_logo = serializers.ImageField(source="organization.logo", read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "organization_name",
            "organization_logo",
            "username",
            "phone_number",
            "role",
            "is_active",
        )
