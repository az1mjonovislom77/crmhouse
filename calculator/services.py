from decimal import ROUND_HALF_UP, Decimal

from rest_framework.exceptions import ValidationError

from calculator.engine import _d, calculate
from calculator.models import CalculatorConfig, GuaranteeOption, SubsidyOption, options_for


def resolve_guarantee(guarantee_id=None, guarantee_key=None, organization=None):
    qs = options_for(GuaranteeOption, organization)
    option = None
    if guarantee_id is not None:
        option = qs.filter(pk=guarantee_id).first()
    elif guarantee_key:
        option = qs.filter(key=guarantee_key).first()
    if option is None:
        raise ValidationError({"guarantee_id": "Kafillik turi topilmadi."})
    return option


def resolve_subsidy(subsidy_id=None, subsidy_key=None, organization=None):
    qs = options_for(SubsidyOption, organization)
    if subsidy_id is not None:
        option = qs.filter(pk=subsidy_id).first()
        if option is None:
            raise ValidationError({"subsidy_id": "Subsidiya turi topilmadi."})
        return option
    if subsidy_key:
        option = qs.filter(key=subsidy_key).first()
        if option is None:
            raise ValidationError({"subsidy_key": "Subsidiya turi topilmadi."})
        return option
    return None


def effective_guarantee_percent(
    *, guarantee_percent, payment_type, manual_down_payment, contract_price, client_payment=None
):
    if manual_down_payment is None or payment_type == "bosh_tolovsiz":
        return guarantee_percent
    contract = _d(contract_price or 0)
    if contract <= 0:
        return guarantee_percent
    paid = client_payment if client_payment is not None else manual_down_payment
    return (_d(paid) * 100 / contract).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute(
    *,
    area,
    price_per_m2,
    payment_type,
    guarantee,
    subsidy,
    credit_years,
    manual_down_payment=None,
    rounding=True,
    config=None,
    renovation_price=0,
):
    config = config or CalculatorConfig.load()
    area_d = _d(area)
    eff_price = _d(price_per_m2)
    if renovation_price and area_d:
        eff_price += _d(renovation_price) / area_d
    return calculate(
        area=area,
        price_per_m2=eff_price,
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
    home = Home.objects.filter(pk=data["home_id"]).first()
    if home is None:
        raise ValidationError({"home_id": "Uy topilmadi."})

    guarantee = resolve_guarantee(data.get("guarantee_id"), data.get("guarantee_key"), organization=organization)
    subsidy = resolve_subsidy(data.get("subsidy_id"), data.get("subsidy_key"), organization=organization)

    price_per_m2 = data.get("price_per_m2") or home.price_per_sqm or config.default_price_per_m2
    result = compute(
        area=home.area,
        price_per_m2=price_per_m2,
        payment_type=data["payment_type"],
        guarantee=guarantee,
        subsidy=subsidy,
        credit_years=data["credit_years"],
        manual_down_payment=data.get("manual_down_payment"),
        rounding=data.get("rounding", True),
        config=config,
        renovation_price=(home.renovation.price if home.renovation else 0),
    )
    result["price_per_m2"] = Decimal(str(price_per_m2))
    result["guarantee_percent"] = effective_guarantee_percent(
        guarantee_percent=guarantee.percent,
        payment_type=data["payment_type"],
        manual_down_payment=data.get("manual_down_payment"),
        contract_price=result.get("contract_price"),
        client_payment=result.get("client_payment"),
    )
    return result


def compute_booking_snapshot(
    *,
    home,
    payment_type,
    guarantee_id=None,
    guarantee_key=None,
    subsidy_id=None,
    subsidy_key=None,
    credit_years,
    manual_down_payment=None,
    rounding=True,
    organization=None,
    price_per_m2=None,
):
    config = CalculatorConfig.for_org(organization)
    guarantee = resolve_guarantee(guarantee_id, guarantee_key, organization=organization)
    subsidy = resolve_subsidy(subsidy_id, subsidy_key, organization=organization)
    area = home.area or 0
    price_per_m2 = price_per_m2 or home.price_per_sqm or config.default_price_per_m2

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
        renovation_price=(home.renovation.price if home.renovation else 0),
    )
    return {
        "price_per_m2": Decimal(str(price_per_m2)),
        "guarantee_percent": effective_guarantee_percent(
            guarantee_percent=guarantee.percent,
            payment_type=payment_type,
            manual_down_payment=manual_down_payment,
            contract_price=result.get("contract_price"),
            client_payment=result.get("client_payment"),
        ),
        **result,
    }
