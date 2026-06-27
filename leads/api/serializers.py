from rest_framework import serializers

from leads.models import Lead, LeadEvent


class LeadEventSerializer(serializers.ModelSerializer):
    by = serializers.StringRelatedField()

    class Meta:
        model = LeadEvent
        fields = ['id', 'type', 'from_value', 'to_value', 'text', 'meeting_at', 'meeting_type', 'by', 'at']


class LeadListSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'full_name', 'phone', 'email', 'source', 'board', 'status', 'sub_status',
            'owner_id', 'owner_name', 'score', 'note', 'created_at', 'updated_at',
        ]


class LeadDetailSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    events = LeadEventSerializer(many=True, read_only=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'full_name', 'phone', 'email', 'source', 'board', 'status', 'sub_status',
            'owner_id', 'owner_name', 'score', 'note', 'created_at', 'updated_at', 'events']


class LeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['full_name', 'phone', 'email', 'source', 'board', 'note']
        extra_kwargs = {'board': {'required': True}}


class LeadUpdateSerializer(serializers.ModelSerializer):
    comment = serializers.CharField(required=False, write_only=True)
    call_result = serializers.CharField(required=False, write_only=True)
    meeting_at = serializers.DateTimeField(required=False, write_only=True)
    meeting_type = serializers.ChoiceField(
        choices=[c[0] for c in LeadEvent.MEETING_TYPE_CHOICES], required=False, write_only=True)

    class Meta:
        model = Lead
        fields = [
            'full_name', 'phone', 'email', 'source', 'note',
            'status', 'sub_status', 'owner',
            'comment', 'call_result', 'meeting_at', 'meeting_type',
        ]

    def validate(self, data):
        if data.get('meeting_at') and not data.get('meeting_type'):
            raise serializers.ValidationError({'meeting_type': 'Bu maydon majburiy'})
        if data.get('meeting_type') and not data.get('meeting_at'):
            raise serializers.ValidationError({'meeting_at': 'Bu maydon majburiy'})
        return data
