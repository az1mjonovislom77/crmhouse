from rest_framework.exceptions import ValidationError
from calculator.formulas.standart import calculate as standart
from calculator.formulas.teng_ulush import calculate as teng_ulush

FORMULAS = {
    'standart': standart,
    'teng_ulush': teng_ulush,
}


def get_formula(key):
    formula = FORMULAS.get(key)
    if formula is None:
        raise ValidationError(f"Noma'lum hisoblash formulasi: {key}")
    return formula
