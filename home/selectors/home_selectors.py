from django.db.models import DecimalField, F, ExpressionWrapper, Value, Case, When
from django.db.models.functions import Coalesce
from home.models import Home


def get_homes_with_finance():
    total_price_expr = (Coalesce(F('area') * F('price_per_sqm'), Value(0)) +
                        Coalesce(F('renovation__price'), Value(0)))

    months_expr = Case(
        When(booking__payment_term__months__gt=0, then=F('booking__payment_term__months')), default=Value(1))

    down_payment_expr = Coalesce(F('booking__down_payment'), Value(0))
    return (
        Home.objects
        .select_related('blocks', 'blocks__projects', 'floor', 'renovation', 'booking', 'booking__payment_term')
        .annotate(
            total_price_annotated=ExpressionWrapper(
                total_price_expr, output_field=DecimalField(max_digits=14, decimal_places=2)),
            initial_payment_annotated=ExpressionWrapper(
                total_price_expr * down_payment_expr / Value(100),
                output_field=DecimalField(max_digits=14, decimal_places=2)),
            monthly_payment_annotated=ExpressionWrapper(
                (total_price_expr - (total_price_expr * down_payment_expr / Value(100))) / months_expr,
                output_field=DecimalField(max_digits=14, decimal_places=2)),
        )
    )
