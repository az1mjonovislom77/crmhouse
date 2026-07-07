from calculator.engine import _d, ceil_step, round_som


def calculate(*, area, price_per_m2, payment_type, guarantee_percent, subsidy_amount,
              credit_years, manual_down_payment=None, rounding=True, config):
    area = _d(area)
    price_per_m2 = _d(price_per_m2)
    g = _d(guarantee_percent) / 100
    S = _d(subsidy_amount)
    Y = int(credit_years)
    step = config.round_step if rounding else 0

    def rnd(v):
        return ceil_step(v, step) if step else _d(v)

    contract = area * price_per_m2

    if manual_down_payment is not None:
        down = _d(manual_down_payment)
    else:
        down = rnd(g * contract)

    client_payment = max(_d(0), down - S)
    credit = contract - down
    months = Y * 12
    monthly_full = round_som(credit / months) if months else _d(0)

    return {
        'contract_price': contract,
        'firm_covers': _d(0),
        'client_payment': client_payment,
        'subsidy_amount': S,
        'credit_amount': credit,
        'monthly_full': monthly_full,
        'monthly_stage1': None,
        'gov_monthly': None,
        'subsidy_years': config.subsidy_years,
        'credit_years': Y,
        'annual_rate_pct': _d(config.annual_rate_pct),
        'state_threshold_pct': _d(config.state_threshold_pct),
        'firm_markup_pct': _d(config.firm_markup_pct),
    }
