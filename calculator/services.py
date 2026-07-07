from decimal import Decimal
from rest_framework.exceptions import ValidationError
from calculator.engine import calculate
from calculator.models import CalculatorConfig, GuaranteeOption, SubsidyOption


def resolve_guarantee(guarantee_id=None, guarantee_key=None):
    qs = GuaranteeOption.objects.all()
    option = None
    if guarantee_id is not None:
        option = qs.filter(pk=guarantee_id).first()
    elif guarantee_key:
        option = qs.filter(key=guarantee_key).first()
    if option is None:
        raise ValidationError({'guarantee_id': 'Kafillik turi topilmadi.'})
    return option


def resolve_subsidy(subsidy_id=None, subsidy_key=None):
    qs = SubsidyOption.objects.all()
    if subsidy_id is not None:
        option = qs.filter(pk=subsidy_id).first()
        if option is None:
            raise ValidationError({'subsidy_id': 'Subsidiya turi topilmadi.'})
        return option
    if subsidy_key:
        option = qs.filter(key=subsidy_key).first()
        if option is None:
            raise ValidationError({'subsidy_key': 'Subsidiya turi topilmadi.'})
        return option
    return None


def compute(*, area, price_per_m2, payment_type, guarantee, subsidy,
            credit_years, manual_down_payment=None, rounding=True, config=None):
    config = config or CalculatorConfig.load()
    return calculate(
        area=area,
        price_per_m2=price_per_m2,
        payment_type=payment_type,
        guarantee_percent=guarantee.percent,
        subsidy_amount=(subsidy.amount if subsidy else 0),
        credit_years=credit_years,
        manual_down_payment=manual_down_payment,
        rounding=rounding,
        config=config,
    )


def calculate_from_payload(data, organization=None):
    from home.models import Home

    config = CalculatorConfig.for_org(organization)

    home = Home.objects.filter(pk=data['home_id']).first()
    if home is None:
        raise ValidationError({'home_id': 'Uy topilmadi.'})

    guarantee = resolve_guarantee(data.get('guarantee_id'), data.get('guarantee_key'))
    subsidy = resolve_subsidy(data.get('subsidy_id'), data.get('subsidy_key'))

    return compute(
        area=home.area,
        price_per_m2=home.price_per_sqm or config.default_price_per_m2,
        payment_type=data['payment_type'],
        guarantee=guarantee,
        subsidy=subsidy,
        credit_years=data['credit_years'],
        manual_down_payment=data.get('manual_down_payment'),
        rounding=data.get('rounding', True),
        config=config,
    )


def compute_booking_snapshot(*, home, payment_type, guarantee_id=None, guarantee_key=None,
                             subsidy_id=None, subsidy_key=None, credit_years,
                             manual_down_payment=None, rounding=True,
                             organization=None):
    config = CalculatorConfig.for_org(organization)
    guarantee = resolve_guarantee(guarantee_id, guarantee_key)
    subsidy = resolve_subsidy(subsidy_id, subsidy_key)

    area = home.area or 0
    price_per_m2 = home.price_per_sqm or config.default_price_per_m2

    result = compute(
        area=area,
        price_per_m2=price_per_m2,
        payment_type=payment_type,
        guarantee=guarantee,
        subsidy=subsidy,
        credit_years=credit_years,
        manual_down_payment=manual_down_payment,
        rounding=rounding,
        config=config,
    )
    return {
        'price_per_m2': Decimal(str(price_per_m2)),
        'guarantee_percent': guarantee.percent,
        **result,
    }
