"""Eslatmalar: bugungi/yaqin to'lovlar, qarzlar va kelishuvlar (quruvchi uchun ro'yxat)."""

from datetime import timedelta

from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from booking.api.serializers import RemindersSerializer
from booking.models import Booking, Commitment
from booking.services.schedule import STATUS_PAID, allocate, build_schedule, down_payment_amount
from common.mixins import filter_by_org
from common.utils import parse_date_param

DEFAULT_WINDOW_DAYS = 7
MAX_WINDOW_DAYS = 90


def _apartment(home):
    if home is None:
        return None
    parts = []
    if home.blocks and home.blocks.title:
        parts.append(f"{home.blocks.title}-blok")
    if home.home_number:
        parts.append(f"{home.home_number}-xonadon")
    if home.floor and home.floor.number is not None:
        parts.append(f"{home.floor.number}-qavat")
    return " · ".join(parts) or None


def _booking_head(booking):
    client = booking.client
    phone = getattr(client, "phone_number", None)
    return {
        "booking_id": booking.id,
        "client": getattr(client, "full_name", None),
        "phone": str(phone) if phone else None,
        "apartment": _apartment(booking.home),
        "contract_no": booking.booking_no,
    }


@extend_schema(
    tags=["Reminders"],
    parameters=[
        OpenApiParameter(name="date", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
        OpenApiParameter(name="days", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY),
    ],
    responses=RemindersSerializer,
)
class RemindersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = parse_date_param(request.query_params.get("date")) or timezone.localdate()
        days = request.query_params.get("days")
        try:
            days = DEFAULT_WINDOW_DAYS if days in (None, "") else int(days)
        except (TypeError, ValueError):
            raise ValidationError({"days": "days butun son bo'lishi kerak."}) from None
        if days < 0 or days > MAX_WINDOW_DAYS:
            raise ValidationError({"days": f"days 0 va {MAX_WINDOW_DAYS} orasida bo'lishi kerak."})
        horizon = today + timedelta(days=days)

        bookings = (
            Booking.objects.filter(status=Booking.BookingStatus.ACTIVE)
            .select_related("client", "home", "home__blocks", "home__floor")
            .prefetch_related("payments")
        )
        bookings = filter_by_org(bookings, request, field="organization")

        overdue, upcoming = [], []
        for booking in bookings:
            schedule = build_schedule(booking)
            if not schedule:
                continue
            allocate(down_payment_amount(booking), schedule, list(booking.payments.all()), today)
            head = _booking_head(booking)
            for installment in schedule:
                if installment.status == STATUS_PAID:
                    continue
                if installment.due_date < today:
                    overdue.append(
                        {
                            **head,
                            "kind": "overdue",
                            "no": installment.no,
                            "due_date": installment.due_date,
                            "amount": installment.remaining,
                            "days": (today - installment.due_date).days,
                            "note": None,
                        }
                    )
                elif installment.due_date <= horizon:
                    upcoming.append(
                        {
                            **head,
                            "kind": "upcoming",
                            "no": installment.no,
                            "due_date": installment.due_date,
                            "amount": installment.remaining,
                            "days": (installment.due_date - today).days,
                            "note": None,
                        }
                    )
                else:
                    # Jadval sanalar bo'yicha tartiblangan — bundan keyingilari oynadan tashqarida.
                    break

        commitments_qs = Commitment.objects.filter(
            status=Commitment.CommitmentStatus.PENDING,
            reminder=True,
            expected_date__lte=horizon,
            booking__status=Booking.BookingStatus.ACTIVE,
        ).select_related("booking", "booking__client", "booking__home", "booking__home__blocks", "booking__home__floor")
        commitments_qs = filter_by_org(commitments_qs, request, field="booking__organization")

        commitments = [
            {
                **_booking_head(commitment.booking),
                "kind": "commitment",
                "no": None,
                "due_date": commitment.expected_date,
                "amount": commitment.amount,
                "days": (commitment.expected_date - today).days,
                "note": commitment.note,
            }
            for commitment in commitments_qs
        ]

        overdue.sort(key=lambda item: item["due_date"])
        upcoming.sort(key=lambda item: item["due_date"])

        return Response(
            {
                "date": today,
                "days": days,
                "counts": {
                    "overdue": len(overdue),
                    "upcoming": len(upcoming),
                    "commitments": len(commitments),
                },
                "overdue": overdue,
                "upcoming": upcoming,
                "commitments": commitments,
            }
        )
