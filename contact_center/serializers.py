from rest_framework import serializers
from contact_center.models import CallRecord


class CRSerializer(serializers.ModelSerializer):
    audio_url = serializers.SerializerMethodField()
    audio_status = serializers.SerializerMethodField()

    class Meta:
        model = CallRecord
        fields = '__all__'

    def get_audio_url(self, obj):
        if obj.audio_file:
            return obj.audio_file.url
        return None

    def get_audio_status(self, obj):
        if obj.audio_downloaded:
            return 'ready'
        elif obj.recordingfile:
            return 'processing'
        return 'none'
