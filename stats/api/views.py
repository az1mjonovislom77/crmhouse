from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from common.mixins import filter_by_org
from stats.selectors.home_selectors import get_sold_events
from stats.selectors.booking_selectors import get_total_contract, get_total_contract_price, get_total_payments, \
    get_total_payments_price, get_total_unpaid
from stats.selectors.lead_selectors import get_total_success_leads, get_total_meetings
from stats.selectors.call_selectors import get_total_calls


@extend_schema(tags=["Stats"])
class StatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("from", str, description="YYYY-MM-DD"),
            OpenApiParameter("to", str, description="YYYY-MM-DD"),
        ],
        responses=inline_serializer("Stats", {
            "sold_homes": serializers.IntegerField(),
            "total_contract": serializers.FloatField(),
            "collected": serializers.FloatField(),
            "debt": serializers.FloatField(),
            "success_leads": serializers.IntegerField(),
            "meetings": serializers.IntegerField(),
            "calls": serializers.IntegerField(),
        }),
    )
    def get(self, request):
        date_from = self._parse_date_param("from")
        date_to = self._parse_date_param("to")

        sold_qs = filter_by_org(
            get_sold_events(date_from, date_to), request,
            field='home__blocks__projects__user__organization',
        )

        booking_qs = filter_by_org(
            get_total_contract(date_from, date_to), request,
            field='home__blocks__projects__user__organization',
        )
        payment_qs = filter_by_org(
            get_total_payments(date_from, date_to), request,
            field='booking__home__blocks__projects__user__organization',
        )

        success_leads_qs = filter_by_org(
            get_total_success_leads(date_from, date_to), request,
            field='owner__organization',
        )
        meetings_qs = filter_by_org(
            get_total_meetings(date_from, date_to), request,
            field='owner__organization',
        )
        calls_qs = filter_by_org(
            get_total_calls(date_from, date_to), request,
            field='user__organization',
        )

        return Response({
            "sold_homes": sold_qs.count(),
            "total_contract": get_total_contract_price(booking_qs),
            "collected": get_total_payments_price(payment_qs),
            "debt": get_total_unpaid(booking_qs),
            "success_leads": success_leads_qs.count(),
            "meetings": meetings_qs.count(),
            "calls": calls_qs.count(),
        })

    def _parse_date_param(self, name):
        value = self.request.query_params.get(name)
        if not value:
            return None
        parsed = parse_date(value)
        if parsed is None:
            raise ValidationError({name: "Noto'g'ri sana formati, YYYY-MM-DD bo'lishi kerak."})
        return parsed
