from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal


def _d(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def ceil_step(value, step):
    value = _d(value)
    step = _d(step)
    if step <= 0:
        return value
    return (value / step).to_integral_value(rounding=ROUND_CEILING) * step


def annuity_factor(annual_rate_pct, years):
    r = float(annual_rate_pct) / 100.0 / 12.0
    n = int(years) * 12
    if n <= 0:
        return 0.0
    if r == 0:
        return 1.0 / n
    p = (1 + r) ** n
    return r * p / (p - 1)


def round_som(value):
    return _d(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP)


_round_som = round_som


def calculate(*, config, **kwargs):
    from calculator.formulas import get_formula

    formula = get_formula(getattr(config, 'formula_key', 'standart'))
    return formula(config=config, **kwargs)
