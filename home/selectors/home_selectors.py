from django.db.models import DecimalField, ExpressionWrapper, F, Value
from django.db.models.functions import Coalesce

from home.models import Home


def get_homes_with_finance():
    total_price_expr = Coalesce(F("area") * F("price_per_sqm"), Value(0)) + Coalesce(F("renovation__price"), Value(0))

    return Home.objects.select_related("blocks", "blocks__projects", "floor", "renovation").annotate(
        total_price_annotated=ExpressionWrapper(
            total_price_expr, output_field=DecimalField(max_digits=14, decimal_places=2)
        ),
    )
