from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.base.views_base import BaseUserViewSet
from common.mixins import filter_by_org
from contracts.api.serializers import ContractSerializer, ContractTemplateSerializer
from contracts.models import Contract, ContractTemplate
from contracts.services.render import (
    extract_placeholders,
    html_to_docx,
    html_to_pdf,
    render_contract_html,
)

DOCX_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


@extend_schema(tags=['ContractTemplate'])
class ContractTemplateViewSet(BaseUserViewSet):
    serializer_class = ContractTemplateSerializer

    def get_queryset(self):
        return filter_by_org(ContractTemplate.objects.all(), self.request)

    def perform_create(self, serializer):
        serializer.save(organization=getattr(self.request.user, 'organization', None))

    @action(detail=True, methods=['get'])
    def placeholders(self, request, pk=None):
        template = self.get_object()
        return Response({'placeholders': extract_placeholders(template.read_html())})


@extend_schema(tags=['Contract'])
class ContractViewSet(BaseUserViewSet):
    serializer_class = ContractSerializer

    def get_queryset(self):
        qs = Contract.objects.select_related('template', 'booking', 'booking__client', 'booking__home')
        return filter_by_org(qs, self.request)

    def perform_create(self, serializer):
        serializer.save(organization=getattr(self.request.user, 'organization', None))

    @extend_schema(responses={200: OpenApiTypes.STR})
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        contract = self.get_object()
        return HttpResponse(render_contract_html(contract), content_type='text/html; charset=utf-8')

    @extend_schema(
        parameters=[OpenApiParameter(name='file_format', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                                     enum=['pdf', 'docx'], default='pdf')],
        responses={(200, 'application/octet-stream'): OpenApiTypes.BINARY})
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        contract = self.get_object()
        file_format = request.query_params.get('file_format', 'pdf')
        if file_format not in ('pdf', 'docx'):
            raise ValidationError({'file_format': "Format 'pdf' yoki 'docx' bo'lishi kerak."})

        html = render_contract_html(contract)
        if file_format == 'pdf':
            content, content_type = html_to_pdf(html), 'application/pdf'
        else:
            content, content_type = html_to_docx(html), DOCX_CONTENT_TYPE

        response = HttpResponse(content, content_type=content_type)
        filename = f"shartnoma-{contract.number or contract.pk}.{file_format}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
