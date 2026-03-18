from rest_framework import serializers


class CommentQuerySerializer(serializers.Serializer):
    media_id = serializers.CharField(required=True)


class ReplySerializer(serializers.Serializer):
    comment_id = serializers.CharField()
    message = serializers.CharField()
