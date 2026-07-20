from decimal import Decimal, InvalidOperation

_BIRLIK = ["", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz"]
_ONLIK = ["", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson"]
_DARAJA = ["", "ming", "million", "milliard", "trillion", "kvadrillion"]


def _uch_xona(n: int) -> str:
    parts = []
    yuz, qoldiq = divmod(n, 100)
    if yuz:
        if yuz > 1:
            parts.append(_BIRLIK[yuz])
        parts.append("yuz")
    on, bir = divmod(qoldiq, 10)
    if on:
        parts.append(_ONLIK[on])
    if bir:
        parts.append(_BIRLIK[bir])
    return " ".join(parts)


def number_to_words_uz(value) -> str:
    """Sonni o'zbekcha so'zlar bilan yozadi: 100000 -> "yuz ming".

    Kasr qismi (tiyin) tashlab yuboriladi. Songa o'xshamagan qiymat
    uchun bo'sh satr qaytaradi.
    """
    try:
        n = int(Decimal(str(value).replace(" ", "").replace("\xa0", "").replace(",", ".")))
    except (InvalidOperation, ValueError, TypeError):
        return ""
    if n == 0:
        return "nol"
    if n < 0:
        return "minus " + number_to_words_uz(-n)
    groups = []
    daraja = 0
    while n:
        n, g = divmod(n, 1000)
        if g:
            if daraja == 1 and g == 1:
                groups.append("ming")
            else:
                groups.append((_uch_xona(g) + " " + _DARAJA[daraja]).strip())
        daraja += 1
    return " ".join(reversed(groups))
