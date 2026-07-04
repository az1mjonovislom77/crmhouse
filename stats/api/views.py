from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from common.mixins import filter_by_org
from common.utils import to_millions
from home.models import Home
from stats.selectors.home_selectors import get_sold_events, get_homes, get_home_status_counts, get_monthly_sales, \
    get_top_sellers, get_block_occupancy
from stats.selectors.booking_selectors import get_total_contract, get_total_contract_price, get_total_payments, \
    get_total_payments_price, get_total_unpaid, get_monthly_revenue
from stats.selectors.lead_selectors import get_leads, get_lead_stats, get_lead_funnel, get_lead_sources, \
    get_success_conversions
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
            "new_clients": serializers.IntegerField(),
            "leads_count": serializers.IntegerField(),
            "home_status": inline_serializer("HomeStatusCounts", {
                status: serializers.IntegerField() for status in Home.HomeStatus.values
            }),
            "monthly_sales": inline_serializer("MonthlySales", {
                "month": serializers.CharField(),
                "sold": serializers.IntegerField(),
            }, many=True),
            "monthly_revenue": inline_serializer("MonthlyRevenue", {
                "month": serializers.CharField(),
                "contract": serializers.FloatField(),
                "collected": serializers.FloatField(),
            }, many=True),
            "lead_funnel": inline_serializer("LeadFunnel", {
                "stage": serializers.CharField(),
                "count": serializers.IntegerField(),
            }, many=True),
            "lead_sources": inline_serializer("LeadSources", {
                "name": serializers.CharField(),
                "value": serializers.IntegerField(),
            }, many=True),
            "top_sellers": inline_serializer("TopSellers", {
                "name": serializers.CharField(),
                "sold": serializers.IntegerField(),
                "revenue": serializers.FloatField(),
            }, many=True),
            "blocks": inline_serializer("BlockOccupancy", {
                "block": serializers.CharField(),
                "total": serializers.IntegerField(),
                "occupied": serializers.IntegerField(),
            }, many=True),
        }),
    )
    def get(self, request):
        date_from = self._parse_date_param("from")
        date_to = self._parse_date_param("to")

        sold_qs = filter_by_org(
            get_sold_events(date_from, date_to), request,
            field='home__blocks__projects__user__organization',
        )
        all_sold_qs = filter_by_org(
            get_sold_events(), request,
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

        lead_qs = filter_by_org(get_leads(), request, field='owner__organization')
        lead_stats = get_lead_stats(lead_qs, date_from, date_to)

        calls_qs = filter_by_org(
            get_total_calls(date_from, date_to), request,
            field='user__organization',
        )
        home_qs = filter_by_org(
            get_homes(), request,
            field='blocks__projects__user__organization',
        )
        all_booking_qs = filter_by_org(
            get_total_contract(), request,
            field='home__blocks__projects__user__organization',
        )
        all_payment_qs = filter_by_org(
            get_total_payments(), request,
            field='booking__home__blocks__projects__user__organization',
        )

        return Response({
            "sold_homes": sold_qs.values('home').distinct().count(),
            "total_contract": to_millions(get_total_contract_price(booking_qs)),
            "collected": to_millions(get_total_payments_price(payment_qs)),
            "debt": to_millions(get_total_unpaid(booking_qs)),
            "success_leads": get_success_conversions(lead_qs, date_from, date_to),
            "meetings": lead_stats['meetings'],
            "calls": calls_qs.count(),
            "new_clients": lead_stats['new'],
            "leads_count": lead_stats['total'],
            "home_status": get_home_status_counts(home_qs),
            "monthly_sales": get_monthly_sales(all_sold_qs),
            "monthly_revenue": get_monthly_revenue(all_booking_qs, all_payment_qs),
            "lead_funnel": get_lead_funnel(lead_qs, date_from, date_to),
            "lead_sources": get_lead_sources(lead_qs, date_from, date_to),
            "top_sellers": get_top_sellers(sold_qs),
            "blocks": get_block_occupancy(home_qs),
        })

    def _parse_date_param(self, name):
        value = self.request.query_params.get(name)
        if not value:
            return None
        parsed = parse_date(value)
        if parsed is None:
            raise ValidationError({name: "Noto'g'ri sana formati, YYYY-MM-DD bo'lishi kerak."})
        return parsed
