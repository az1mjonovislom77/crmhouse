from django import template

from common.services.numbers import number_to_words_uz

register = template.Library()


@register.filter(name="sozda")
def sozda(value):
    return number_to_words_uz(value)
