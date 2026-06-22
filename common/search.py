from django.db.models import Q
from rest_framework.filters import SearchFilter

APOSTROPHES = ("'", "`", "‘", "’", "ʼ", "ʻ")
CANONICAL_APOSTROPHE = "'"
LATIN_TO_CYRILLIC_PAIRS = (("o'", "ў"), ("g'", "ғ"), ("sh", "ш"), ("ch", "ч"), ("ya", "я"), ("yo", "ё"), ("yu", "ю"))

LATIN_TO_CYRILLIC_CHARS = {
    "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ", "i": "и", "j": "ж", "k": "к", "l": "л",
    "m": "м", "n": "н", "o": "о", "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "x": "х",
    "y": "й", "z": "з",
}

CYRILLIC_TO_LATIN_CHARS = {
    "а": "a", "б": "b", "д": "d", "е": "e", "ф": "f", "г": "g", "ҳ": "h", "и": "i", "ж": "j", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "қ": "q", "р": "r", "с": "s", "т": "t", "у": "u", "в": "v", "х": "x",
    "й": "y", "з": "z", "ш": "sh", "ч": "ch", "я": "ya", "ё": "yo", "ю": "yu", "ў": "o'", "ғ": "g'",
}


def normalize_uzbek_apostrophes(text):
    for apostrophe in APOSTROPHES:
        text = text.replace(apostrophe, CANONICAL_APOSTROPHE)
    return text


def latin_to_cyrillic(text):
    text = normalize_uzbek_apostrophes(text.lower())

    for latin, cyrillic in LATIN_TO_CYRILLIC_PAIRS:
        text = text.replace(latin, cyrillic)

    return "".join(LATIN_TO_CYRILLIC_CHARS.get(char, char) for char in text)


def cyrillic_to_latin(text):
    return "".join(CYRILLIC_TO_LATIN_CHARS.get(char, char) for char in text.lower())


def get_transliterated_search_terms(text):
    terms = [
        text,
        normalize_uzbek_apostrophes(text),
        cyrillic_to_latin(text),
        latin_to_cyrillic(text),
    ]

    expanded_terms = []
    for term in terms:
        expanded_terms.append(term)
        normalized = normalize_uzbek_apostrophes(term)
        for apostrophe in APOSTROPHES:
            expanded_terms.append(normalized.replace(CANONICAL_APOSTROPHE, apostrophe))

    return list(dict.fromkeys(term for term in expanded_terms if term))


def build_transliterated_search_q(fields, search):
    query = Q()
    for field in fields:
        for term in get_transliterated_search_terms(search):
            query |= Q(**{f"{field}__icontains": term})
    return query


class TransliteratedSearchFilter(SearchFilter):
    def construct_search(self, field_name, queryset=None):
        lookup_prefixes = {"^": "istartswith", "=": "iexact", "@": "search", "$": "iregex"}
        lookup = lookup_prefixes.get(field_name[0], "icontains")

        if field_name[0] in lookup_prefixes:
            field_name = field_name[1:]

        return f"{field_name}__{lookup}"

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_search_fields(view, request)
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(str(search_field), queryset)
            for search_field in search_fields
        ]

        for search_term in search_terms:
            term_query = Q()
            for orm_lookup in orm_lookups:
                for variant in get_transliterated_search_terms(search_term):
                    term_query |= Q(**{orm_lookup: variant})
            queryset = queryset.filter(term_query)

        if self.must_call_distinct(queryset, search_fields):
            queryset = queryset.distinct()

        return queryset
