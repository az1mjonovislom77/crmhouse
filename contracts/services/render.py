import os
import re
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.db import models
from django.template import Context, Engine
from html4docx import HtmlToDocx
from xhtml2pdf import pisa
from xhtml2pdf.files import pisaFileObject

from common.services.numbers import number_to_words_uz
from contracts.models import Contract

_TEMPLATE_ENGINE = Engine(builtins=["contracts.templatetags.contracts_extras"])

_orig_get_named_file = pisaFileObject.getNamedFile


def _get_named_file(self):
    uri = str(self.uri or "")
    if os.path.isfile(uri):
        return uri
    return _orig_get_named_file(self)


pisaFileObject.getNamedFile = _get_named_file

PLACEHOLDER_RE = re.compile(r"{{\s*([\w.]+)\s*}}")

_FONT_DIR = Path(settings.BASE_DIR) / "static" / "fonts"

_PDF_BASE_CSS = """
<style>
@font-face {{ font-family: "DejaVuSans"; src: url("{regular}"); }}
@font-face {{ font-family: "DejaVuSans"; src: url("{bold}"); font-weight: bold; }}
@font-face {{ font-family: "DejaVuSans"; src: url("{italic}"); font-style: italic; }}
@font-face {{ font-family: "DejaVuSans"; src: url("{bold_italic}"); font-weight: bold; font-style: italic; }}
body {{ font-family: "DejaVuSans"; }}
</style>
""".format(
    regular=(_FONT_DIR / "DejaVuSans.ttf").as_posix(),
    bold=(_FONT_DIR / "DejaVuSans-Bold.ttf").as_posix(),
    italic=(_FONT_DIR / "DejaVuSans-Oblique.ttf").as_posix(),
    bold_italic=(_FONT_DIR / "DejaVuSans-BoldOblique.ttf").as_posix(),
)


def extract_placeholders(html: str) -> list[str]:
    return sorted(set(PLACEHOLDER_RE.findall(html)))


class BlankNoneWrapper:
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        value = getattr(self._obj, name)
        if value is None:
            return ""
        if isinstance(value, models.Model):
            return BlankNoneWrapper(value)
        return value

    def __str__(self):
        return str(self._obj)


def _wrap(value):
    if isinstance(value, models.Model):
        return BlankNoneWrapper(value)
    if value is None:
        return ""
    return value


def build_context(contract: Contract) -> dict:
    ctx = dict(contract.data or {})
    for key, value in list(ctx.items()):
        words = number_to_words_uz(value)
        if words:
            ctx.setdefault(f"{key}_sozda", words)
    booking = contract.booking
    if booking is not None:
        ctx.setdefault("booking", booking)
        ctx.setdefault("client", booking.client)
        ctx.setdefault("home", booking.home)
        ctx.setdefault("company", booking.company)
        ctx.setdefault("total_price", booking.total_price)
        ctx.setdefault("total_price_sozda", booking.total_price_inword)
    ctx.setdefault("contract", contract)
    return {key: _wrap(value) for key, value in ctx.items()}


def render_contract_html(contract: Contract) -> str:
    source = contract.template.read_html()
    return _TEMPLATE_ENGINE.from_string(source).render(Context(build_context(contract)))


def html_to_pdf(html: str) -> bytes:
    if "</head>" in html:
        html = html.replace("</head>", _PDF_BASE_CSS + "</head>", 1)
    else:
        html = _PDF_BASE_CSS + html
    buffer = BytesIO()
    result = pisa.CreatePDF(src=html, dest=buffer, encoding="utf-8")
    if result.err:
        raise ValueError("PDF generatsiya qilishda xatolik yuz berdi.")
    return buffer.getvalue()


def html_to_docx(html: str) -> bytes:
    document = HtmlToDocx().parse_html_string(html)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
