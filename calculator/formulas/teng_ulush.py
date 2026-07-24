from decimal import Decimal

from calculator.engine import _d, annuity_factor, ceil_step, round_som

# Bank ajratadigan kredit uchun yagona maksimal limit (hududga bog'liq emas)
KREDIT_LIMIT = Decimal('380000000')
# 200 mln gacha bo'lgan tannarxda 15% bosh to'lov 5% ga tushiriladi
DISCOUNT_THRESHOLD = Decimal('200000000')
DISCOUNT_PERCENT = Decimal('0.05')
# Pedagog subsidiyasi: kredit summasidan hisoblanadi — (kredit / 0.85) * 0.15 * 0.25
PEDAGOG_KOEF = (Decimal('0.15') * Decimal('0.25')) / Decimal('0.85')


def calculate(*, area, price_per_m2, payment_type, guarantee_percent, subsidy_amount,
              credit_years, manual_down_payment=None, rounding=True, config,
              subsidy_key=None):
    area = _d(area)
    price_per_m2 = _d(price_per_m2)
    g = _d(guarantee_percent) / 100
    manual = _d(manual_down_payment or 0)
    soliq = 1 + _d(config.firm_markup_pct) / 100
    R = _d(config.annual_rate_pct)
    T = _d(config.state_threshold_pct)
    Y = int(credit_years)
    step = config.round_step if rounding else 0

    tannarx = area * price_per_m2

    is_pedagog = subsidy_key == 'pedagog'
    is_oddiy = (not is_pedagog) and _d(subsidy_amount) > 0
    fixed_sub = _d(subsidy_amount) if is_oddiy else _d(0)

    def rnd(v):
        return ceil_step(v, step) if step else _d(v)

    if not is_pedagog and tannarx <= DISCOUNT_THRESHOLD and g == Decimal('0.15'):
        g = DISCOUNT_PERCENT

    sub = _d(0)
    contract = tannarx
    firm_covers = _d(0)
    client_payment = _d(0)
    credit = _d(0)

    # Pedagogda kredit va subsidiya bir-biriga bog'liq — mos kelguncha iteratsiya,
    # boshqa holatlarda birinchi aylanishdayoq tugaydi.
    for _ in range(60):
        const_sub = fixed_sub if is_oddiy else (sub if is_pedagog else _d(0))

        if payment_type == 'bosh_tolovsiz':
            num = tannarx * g - manual - const_sub
            den = 1 - soliq * g
            firm_covers = num / den if num > 0 else _d(0)
            contract = rnd(tannarx + firm_covers * soliq)
            jami_bosh = contract * g
            firm_covers = max(_d(0), jami_bosh - manual - const_sub)
            client_payment = manual
            credit = max(_d(0), contract - client_payment - firm_covers - const_sub)
        else:
            contract = tannarx
            firm_covers = _d(0)
            min_bosh = max(_d(0), contract * g - const_sub)
            client_payment = max(manual, min_bosh)
            credit = max(_d(0), contract - client_payment - const_sub)

        if is_pedagog:
            new_sub = credit * PEDAGOG_KOEF
            converged = abs(new_sub - sub) < 1
            sub = new_sub
            if converged:
                break
        else:
            sub = fixed_sub
            break

    if credit > KREDIT_LIMIT:
        client_payment += credit - KREDIT_LIMIT
        credit = KREDIT_LIMIT
        if is_pedagog:
            sub = credit * PEDAGOG_KOEF

    if step:
        if firm_covers > 0:
            firm_covers = ceil_step(firm_covers, step)
        if client_payment > 0:
            client_payment = ceil_step(client_payment, step)

    monthly_full = round_som(credit * _d(annuity_factor(R, Y)))

    # Foiz stavkasi bo'yicha davlat yordami faqat "oddiy" subsidiyada:
    # dastlabki bosqichda mijoz pastroq stavkada to'laydi, farqni davlat qoplaydi.
    # Pedagogda yordam faqat bosh to'lov qismiga — kredit to'liq stavkada to'lanadi.
    if is_oddiy and credit > 0:
        monthly_stage1 = round_som(credit * _d(annuity_factor(T, Y)))
        gov_monthly = monthly_full - monthly_stage1
    else:
        monthly_stage1 = None
        gov_monthly = None

    return {
        'contract_price': contract,
        'firm_covers': firm_covers,
        'client_payment': client_payment,
        'subsidy_amount': sub,
        'credit_amount': credit,
        'monthly_full': monthly_full,
        'monthly_stage1': monthly_stage1,
        'gov_monthly': gov_monthly,
        'subsidy_years': config.subsidy_years,
        'credit_years': Y,
        'annual_rate_pct': R,
        'state_threshold_pct': T,
        'firm_markup_pct': _d(config.firm_markup_pct),
    }
