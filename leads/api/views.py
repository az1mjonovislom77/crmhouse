import json
import re
import httpx
from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from common.base.views_base import BaseUserViewSet
from leads.api.serializers import LeadCreateSerializer, LeadDetailSerializer, LeadListSerializer, LeadUpdateSerializer
from leads.selectors.lead_selectors import filter_leads, get_lead_detail_queryset, get_lead_list_queryset, get_status_counts
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
        if self.action == 'retrieve':
            return get_lead_detail_queryset()
        return get_lead_list_queryset()

    def get_serializer_class(self):
        if self.action == 'create':
            return LeadCreateSerializer
        if self.action in ('update', 'partial_update'):
            return LeadUpdateSerializer
        if self.action == 'retrieve':
            return LeadDetailSerializer
        return LeadListSerializer

    def list(self, request, *args, **kwargs):
        # Status filtrisiz queryset — counts uchun (boshqa filtrlar saqlanadi)
        count_params = request.query_params.copy()
        count_params._mutable = True
        count_params.pop('status', None)
        counts = get_status_counts(filter_leads(self.get_queryset(), count_params))

        qs = filter_leads(self.get_queryset(), request.query_params)
        page = self.paginate_queryset(qs)
        if page is not None:
            response = self.get_paginated_response(LeadListSerializer(page, many=True).data)
            response.data['counts'] = counts
            return response
        return Response({'counts': counts, 'data': LeadListSerializer(qs, many=True).data})

    def create(self, request, *args, **kwargs):
        serializer = LeadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = LeadService.create_lead(serializer.validated_data, request.user)
        return Response(LeadDetailSerializer(get_lead_detail_queryset().get(pk=lead.pk)).data,
                        status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = LeadUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        lead = LeadService.update_lead(instance, serializer.validated_data, request.user)
        return Response(LeadDetailSerializer(get_lead_detail_queryset().get(pk=lead.pk)).data)

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
        lead = get_lead_detail_queryset().get(pk=pk)

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
