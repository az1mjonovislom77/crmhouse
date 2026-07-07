from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from calculator.api.serializers import (
    CalculateInputSerializer, CalculatorConfigSerializer,
    GuaranteeOptionSerializer, SubsidyOptionSerializer,
)
from calculator.models import CalculatorConfig, GuaranteeOption, SubsidyOption
from calculator.services import calculate_from_payload
from common.permissions import IsAdminOrReadOnly


def _org(request):
    return getattr(request.user, 'organization', None)


@extend_schema(tags=['Calculator'])
class CalculatorConfigView(RetrieveUpdateAPIView):
    serializer_class = CalculatorConfigSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    http_method_names = ['get', 'put']

    def get_object(self):
        return CalculatorConfig.resolve_for_edit(_org(self.request))


class _OrgScopedOptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    http_method_names = ['get', 'post', 'put', 'delete']
    pagination_class = None

    def get_queryset(self):
        return self.model.objects.filter(organization=_org(self.request))

    def perform_create(self, serializer):
        serializer.save(organization=_org(self.request))


@extend_schema(tags=['Calculator'])
class GuaranteeOptionViewSet(_OrgScopedOptionViewSet):
    model = GuaranteeOption
    serializer_class = GuaranteeOptionSerializer


@extend_schema(tags=['Calculator'])
class SubsidyOptionViewSet(_OrgScopedOptionViewSet):
    model = SubsidyOption
    serializer_class = SubsidyOptionSerializer


@extend_schema(tags=['Calculator'], request=CalculateInputSerializer)
class CalculateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CalculateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = calculate_from_payload(serializer.validated_data, organization=_org(request))
        return Response(result)
