from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from common.base.serializers_base import BaseReadSerializer
from tasks.models import Card, Project, Comment
from tasks.services.project import create_project, update_project
from user.api.serializers.user_serializers import UserMiniSerializer


class CardSerializer(BaseReadSerializer):
    created_by = UserMiniSerializer(read_only=True)
    updated_by = UserMiniSerializer(read_only=True)

    class Meta(BaseReadSerializer.Meta):
        model = Card
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class CommentSerializer(BaseReadSerializer):
    created_by = UserMiniSerializer(read_only=True)
    updated_by = UserMiniSerializer(read_only=True)

    class Meta(BaseReadSerializer.Meta):
        model = Comment
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class ProjectGetSerializer(serializers.ModelSerializer):
    users_full_name = SerializerMethodField()
    card_title = serializers.CharField(source='card.title', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    created_by = UserMiniSerializer(read_only=True)
    updated_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'users', 'description', 'comments', 'users_full_name', 'card', 'card_title', 'title', 'order',
                  'created_by', 'updated_by')
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_users_full_name(self, obj):
        return [user.full_name for user in obj.users.all()]


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('users', 'description', 'card', 'title')
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def create(self, validated_data):
        users = validated_data.pop('users', [])
        card = validated_data.pop('card')

        return create_project(card=card, users=users, order=None, **validated_data)


class ProjectUpdateSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)

    class Meta:
        model = Project
        fields = ('users', 'description', 'card', 'title', 'order')
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
        validators = []

    def validate_order(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("Order >= 1 bo‘lishi kerak")
        return value

    def update(self, instance, validated_data):
        users = validated_data.pop('users', None)
        new_card = validated_data.pop('card', None)
        new_order = validated_data.pop('order', None)

        updated = update_project(instance, new_card=new_card, new_order=new_order, users=users, **validated_data)

        return {"updated": updated}
