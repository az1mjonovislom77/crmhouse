from django.db import transaction
from user.models import User


class UserService:

    @staticmethod
    @transaction.atomic
    def create_user(validated_data):
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save(update_fields=["password"])
        return user

    @staticmethod
    @transaction.atomic
    def update_user(instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
