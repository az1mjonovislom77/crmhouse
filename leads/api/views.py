import json
import re

import httpx
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from common.base.views_base import BaseUserViewSet
from common.mixins import filter_by_org
from leads.api.serializers import (
    LeadBulkAssignSerializer,
    LeadCreateSerializer,
    LeadDetailSerializer,
    LeadListSerializer,
    LeadNotificationSerializer,
    LeadUpdateSerializer,
)
from leads.models import LeadNotification
from leads.selectors.lead_selectors import (
    filter_leads,
    get_lead_detail_queryset,
    get_lead_list_queryset,
    get_status_counts,
    scope_leads_for_user,
)
from leads.services.lead_service import LeadService


class LeadPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)
        return Response({
            'page': self.page.number,
            'limit': limit,
            'total': total,
            'total_pages': (total + limit - 1) // limit,
            'data': data,
        })


@extend_schema(tags=['Leads'])
class LeadViewSet(BaseUserViewSet):
    pagination_class = LeadPagination

    def get_queryset(self):
        if self.action in ('retrieve', 'ai_suggest'):
            qs = get_lead_detail_queryset()
        else:
            qs = get_lead_list_queryset()
        qs = filter_by_org(qs, self.request, field='owner__organization')
        return scope_leads_for_user(qs, self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return LeadCreateSerializer
        if self.action in ('update', 'partial_update'):
            return LeadUpdateSerializer
        if self.action == 'retrieve':
            return LeadDetailSerializer
        if self.action == 'bulk_assign':
            return LeadBulkAssignSerializer
        return LeadListSerializer

    def list(self, request, *args, **kwargs):
        count_params = request.query_params.copy()
        count_params._mutable = True
        count_params.pop('status', None)
        base_qs = self.get_queryset()
        counts = get_status_counts(filter_leads(base_qs, count_params, user=request.user), user=request.user)

        qs = filter_leads(base_qs, request.query_params, user=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            response = self.get_paginated_response(LeadListSerializer(page, many=True).data)
            response.data['counts'] = counts
            return response
        return Response({'counts': counts, 'data': LeadListSerializer(qs, many=True).data})

    def create(self, request, *args, **kwargs):
        serializer = LeadCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        lead = LeadService.create_lead(serializer.validated_data, request.user)
        return Response(LeadDetailSerializer(get_lead_detail_queryset().get(pk=lead.pk),
                                             context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = LeadUpdateSerializer(instance, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        lead = LeadService.update_lead(instance, serializer.validated_data, request.user)
        return Response(LeadDetailSerializer(get_lead_detail_queryset().get(pk=lead.pk),
                                             context={'request': request}).data)

    @extend_schema(
        request=LeadBulkAssignSerializer,
        responses={200: inline_serializer('LeadBulkAssignResponse', fields={
            'updated': serializers.IntegerField(),
            'lead_ids': serializers.ListField(child=serializers.IntegerField()),
            'assignee_id': serializers.IntegerField(),
            'assignee_name': serializers.CharField(),
        })},
    )
    @action(detail=False, methods=['post'], url_path='bulk-assign')
    def bulk_assign(self, request):
        serializer = LeadBulkAssignSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        assignee_to = serializer.validated_data['assignee_to']
        lead_ids = serializer.validated_data['lead_ids']
        updated_ids = LeadService.bulk_assign_leads(
            lead_ids, assignee_to, request.user, self.get_queryset(),
        )
        return Response({
            'updated': len(updated_ids),
            'lead_ids': updated_ids,
            'assignee_id': assignee_to.id,
            'assignee_name': assignee_to.full_name,
        })

    @extend_schema(
        request=None,
        responses={200: inline_serializer('AiSuggestResponse', fields={
            'tips': serializers.ListField(child=serializers.CharField()),
            'suggested_message': serializers.CharField(allow_null=True),
            'next_action': serializers.CharField(allow_null=True),
        })},
    )
    @action(detail=True, methods=['post'], url_path='ai-suggest')
    def ai_suggest(self, request, pk=None):
        lead = self.get_object()

        events_text = '\n'.join([
            f"- [{e.at.strftime('%Y-%m-%d %H:%M')}] {e.type}"
            f"{f': {e.from_value} → {e.to_value}' if e.from_value or e.to_value else ''}"
            f"{f' | {e.text}' if e.text else ''}"
            f" ({e.by})"
            for e in lead.events.all()
        ]) or "Hali hech qanday amal yo'q"

        note_str = lead.note or "yo'q"
        prompt = (
            "Sen ko'chmas mulk sotuv bo'yicha yordamchisan.\n"
            "Quyidagi lead ma'lumotlariga qarab maslahat ber:\n\n"
            f"Mijoz: {lead.full_name} | Manba: {lead.source}\n"
            f"Board: {lead.board} | Status: {lead.status}/{lead.sub_status or '-'}\n"
            f"Izoh: {note_str}\n\n"
            f"Tarix:\n{events_text}\n\n"
            "O'zbek tilida 3-5 ta qisqa, amaliy maslahat ber. Faqat JSON:\n"
            '{"tips":["..."],"suggested_message":"...","next_action":"call|meeting|comment"}'
        )

        api_key = getattr(settings, 'GROQ_API_KEY', None)
        if not api_key:
            return Response({'error': "GROQ_API_KEY sozlanmagan"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            resp = httpx.post('https://api.groq.com/openai/v1/chat/completions',
                              headers={
                                  'Authorization': f'Bearer {api_key}',
                                  'content-type': 'application/json',
                              },
                              json={
                                  'model': 'llama-3.3-70b-versatile',
                                  'max_tokens': 1024,
                                  'messages': [{'role': 'user', 'content': prompt}]}, timeout=30)
            resp.raise_for_status()
            content = resp.json()['choices'][0]['message']['content']
            match = re.search(r'\{.*\}', content, re.DOTALL)
            return Response(
                json.loads(match.group()) if match
                else {'tips': [content], 'suggested_message': None, 'next_action': None}
            )
        except httpx.HTTPStatusError:
            return Response({'error': 'AI xizmatiga ulanishda xato'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            return Response({'error': 'AI javob qaytarishda xato'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Notifications'])
class LeadNotificationViewSet(BaseUserViewSet):
    serializer_class = LeadNotificationSerializer
    http_method_names = ['get']

    def get_queryset(self):
        today = timezone.now().date()
        return LeadNotification.objects.filter(
            owner=self.request.user,
            meeting_at__date=today,
        ).select_related('lead')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = LeadNotificationSerializer(queryset, many=True).data
        return Response(data)
