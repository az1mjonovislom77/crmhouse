from calculator.engine import _d, annuity_factor, ceil_step, round_som


def calculate(
    *,
    area,
    price_per_m2,
    payment_type,
    guarantee_percent,
    subsidy_amount,
    credit_years,
    manual_down_payment=None,
    rounding=True,
    config,
):
    area = _d(area)
    price_per_m2 = _d(price_per_m2)
    g = _d(guarantee_percent) / 100
    S = _d(subsidy_amount)
    m = _d(config.firm_markup_pct) / 100
    R = _d(config.annual_rate_pct)
    T = _d(config.state_threshold_pct)
    Y = int(credit_years)
    step = config.round_step if rounding else 0

    def rnd(v):
        return ceil_step(v, step) if step else _d(v)

    base = area * price_per_m2

    if payment_type == "bosh_tolovsiz":
        eff = base - (1 + m) * S
        contract = rnd(eff / (1 - g * (1 + m)))
        firm_covers = rnd(g * contract - S)
        client_payment = _d(0) if S > 0 else rnd(firm_covers * m)
        credit = contract - firm_covers - client_payment - S
    else:
        contract = base
        full_initial = rnd(g * contract)
        firm_covers = _d(0)
        if manual_down_payment is not None:
            M = _d(manual_down_payment)
            client_payment = M
            credit = contract - M - S
        else:
            client_payment = max(_d(0), full_initial - S)
            credit = contract - full_initial

    monthly_full = round_som(credit * _d(annuity_factor(R, Y)))

    if S > 0:
        monthly_stage1 = round_som(credit * _d(annuity_factor(T, Y)))
        gov_monthly = monthly_full - monthly_stage1
    else:
        monthly_stage1 = None
        gov_monthly = None

    return {
        "contract_price": contract,
        "firm_covers": firm_covers,
        "client_payment": client_payment,
        "subsidy_amount": S,
        "credit_amount": credit,
        "monthly_full": monthly_full,
        "monthly_stage1": monthly_stage1,
        "gov_monthly": gov_monthly,
        "subsidy_years": config.subsidy_years,
        "credit_years": Y,
        "annual_rate_pct": R,
        "state_threshold_pct": T,
        "firm_markup_pct": _d(config.firm_markup_pct),
    }
