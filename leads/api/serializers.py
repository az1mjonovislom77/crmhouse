from django.contrib.auth import get_user_model
from rest_framework import serializers

from leads.models import Lead, LeadEvent, LeadNotification

User = get_user_model()


class LeadEventSerializer(serializers.ModelSerializer):
    by = serializers.StringRelatedField()

    class Meta:
        model = LeadEvent
        fields = ['id', 'type', 'from_value', 'to_value', 'text', 'meeting_at', 'meeting_type', 'subsidiya', 'by', 'at']


class LeadListSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'full_name', 'phone', 'email', 'source', 'board', 'status', 'sub_status',
            'owner_id', 'owner_name', 'score', 'note',
            'meeting_at', 'meeting_type', 'subsidiya', 'contacted_at', 'created_at', 'updated_at',
        ]


class LeadDetailSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    events = LeadEventSerializer(many=True, read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'full_name', 'phone', 'email', 'source', 'board', 'status', 'sub_status',
            'owner_id', 'owner_name', 'score', 'note', 'meeting_at', 'meeting_type', 'subsidiya',
            'contacted_at', 'created_at', 'updated_at', 'events']


class LeadCreateSerializer(serializers.ModelSerializer):
    meeting_at = serializers.DateTimeField(required=False, write_only=True)
    meeting_type = serializers.ChoiceField(
        choices=[c[0] for c in LeadEvent.MEETING_TYPE_CHOICES], required=False, write_only=True)

    class Meta:
        model = Lead
        fields = ['full_name', 'phone', 'email', 'source', 'board', 'note', 'subsidiya', 'meeting_at', 'meeting_type']
        extra_kwargs = {'board': {'required': True}}

    def validate(self, data):
        if data.get('meeting_at') and not data.get('meeting_type'):
            raise serializers.ValidationError({'meeting_type': 'Bu maydon majburiy'})
        if data.get('meeting_type') and not data.get('meeting_at'):
            raise serializers.ValidationError({'meeting_at': 'Bu maydon majburiy'})
        return data


class LeadNotificationSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source='lead.full_name', read_only=True)
    lead_phone = serializers.CharField(source='lead.phone', read_only=True)

    class Meta:
        model = LeadNotification
        fields = ['id', 'lead_id', 'lead_name', 'lead_phone', 'meeting_at', 'created_at']
        read_only_fields = ['id', 'lead_id', 'lead_name', 'lead_phone', 'meeting_at', 'created_at']


class LeadUpdateSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    comment = serializers.CharField(required=False, write_only=True)
    call_result = serializers.CharField(required=False, write_only=True)
    meeting_at = serializers.DateTimeField(required=False, write_only=True)
    meeting_type = serializers.ChoiceField(
        choices=[c[0] for c in LeadEvent.MEETING_TYPE_CHOICES], required=False, write_only=True)

    class Meta:
        model = Lead
        fields = [
            'full_name', 'phone', 'email', 'source', 'note', 'subsidiya',
            'status', 'sub_status', 'owner',
            'comment', 'call_result', 'meeting_at', 'meeting_type',
        ]

    def validate(self, data):
        if data.get('meeting_at') and not data.get('meeting_type'):
            raise serializers.ValidationError({'meeting_type': 'Bu maydon majburiy'})
        if data.get('meeting_type') and not data.get('meeting_at'):
            raise serializers.ValidationError({'meeting_at': 'Bu maydon majburiy'})
        return data
