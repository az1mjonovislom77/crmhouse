from rest_framework import serializers
from user.models import RequestLog
from user.api.serializers.user_serializers import UserMiniSerializer


class RequestLogSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = RequestLog
        fields = ['id', 'user', 'method', 'path', 'status_code', 'duration_ms', 'ip_address', 'created_at']
