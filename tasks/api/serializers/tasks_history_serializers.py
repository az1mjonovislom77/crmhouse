from rest_framework import serializers

from tasks.models import Card, Comment, Project


class BaseHistorySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()

    def get_user(self, obj):
        return obj.history_user.full_name if obj.history_user else None

    def get_action(self, obj):
        return {"+": "created", "~": "updated", "-": "deleted"}.get(obj.history_type)


class ProjectHistorySerializer(BaseHistorySerializer):
    class Meta:
        model = Project.history.model
        fields = ["history_date", "user", "action", "title"]


class CardHistorySerializer(BaseHistorySerializer):
    class Meta:
        model = Card.history.model
        fields = ["history_date", "user", "action", "title"]


class CommentHistorySerializer(BaseHistorySerializer):
    class Meta:
        model = Comment.history.model
        fields = ["history_date", "user", "action", "text"]
