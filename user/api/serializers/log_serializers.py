from rest_framework import serializers

from user.api.serializers.user_serializers import UserMiniSerializer
from user.models import RequestLog


class RequestLogSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = RequestLog
        fields = ['id', 'user', 'method', 'path', 'status_code', 'duration_ms', 'ip_address', 'created_at']
