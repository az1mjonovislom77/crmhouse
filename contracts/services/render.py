import os
import re
from io import BytesIO
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString
from django.conf import settings
from django.db import models
from django.template import Context, Engine
from docx.shared import Cm, Pt
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

_FONT_FACES = {
    "regular": (_FONT_DIR / "DejaVuSans.ttf").as_posix(),
    "bold": (_FONT_DIR / "DejaVuSans-Bold.ttf").as_posix(),
    "italic": (_FONT_DIR / "DejaVuSans-Oblique.ttf").as_posix(),
    "bold_italic": (_FONT_DIR / "DejaVuSans-BoldOblique.ttf").as_posix(),
}

# xhtml2pdf faqat o'zi ro'yxatdan o'tgan shriftlarni ishlata oladi; shablonlarda
# uchraydigan keng tarqalgan shrift nomlarini DejaVu'ga bog'laymiz, aks holda
# kirill matni Helvetica fallback tufayli kvadratlarga aylanadi.
_PDF_FONT_ALIASES = (
    "DejaVuSans",
    "DejaVu Sans",
    "Arial",
    "Helvetica",
    "Calibri",
    "Cambria",
    "Verdana",
    "Tahoma",
    "Georgia",
    "Segoe UI",
    "Times New Roman",
    "Times",
    "sans-serif",
    "serif",
)

_PDF_PAGE_CSS = '@page { size: A4; margin: 2cm; } body { font-family: "DejaVuSans"; font-size: 12pt; }'

_HEAD_TAG_RE = re.compile(r"<head[^>]*>", re.IGNORECASE)

_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_CSS_AT_BLOCK_RE = re.compile(r"@[\w-]+[^{}]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", re.DOTALL)
_CSS_AT_LINE_RE = re.compile(r"@[^{};]*;")
_CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_IMPORTANT_RE = re.compile(r"\s*!important\s*", re.IGNORECASE)

# Ota elementdan bolalarga meros bo'lib o'tadigan CSS xususiyatlar
_INHERITED_PROPS = frozenset({
    "color",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "letter-spacing",
    "line-height",
    "text-align",
    "text-indent",
    "text-transform",
})

# Brauzer standart stillari — HTML ko'rinishini DOCX'da ham saqlash uchun
_UA_DEFAULT_RULES = (
    ("h1", {"font-size": "24pt", "font-weight": "bold", "color": "#000000"}),
    ("h2", {"font-size": "18pt", "font-weight": "bold", "color": "#000000"}),
    ("h3", {"font-size": "14pt", "font-weight": "bold", "color": "#000000"}),
    ("h4", {"font-size": "12pt", "font-weight": "bold", "color": "#000000"}),
    ("h5", {"font-size": "10pt", "font-weight": "bold", "color": "#000000"}),
    ("h6", {"font-size": "8pt", "font-weight": "bold", "color": "#000000"}),
    ("th", {"text-align": "center"}),
    ("center", {"text-align": "center"}),
)

_GENERIC_FONT_MAP = {
    "sans-serif": "Arial",
    "serif": "Times New Roman",
    "monospace": "Courier New",
    "dejavusans": "DejaVu Sans",
}

_CSS_SIZE_RE = re.compile(r"([\d.]+)\s*(px|pt|em|rem|%)?")


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


# --- PDF ---

def _font_face_css(family: str) -> str:
    return (
        f'@font-face {{ font-family: "{family}"; src: url("{_FONT_FACES["regular"]}"); }}'
        f'@font-face {{ font-family: "{family}"; src: url("{_FONT_FACES["bold"]}"); font-weight: bold; }}'
        f'@font-face {{ font-family: "{family}"; src: url("{_FONT_FACES["italic"]}"); font-style: italic; }}'
        f'@font-face {{ font-family: "{family}"; src: url("{_FONT_FACES["bold_italic"]}");'
        f" font-weight: bold; font-style: italic; }}"
    )


def _build_pdf_base_css(html: str) -> str:
    html_lower = html.lower()
    faces = [
        _font_face_css(family)
        for family in _PDF_FONT_ALIASES
        if family == "DejaVuSans" or family.lower() in html_lower
    ]
    return "<style>" + "".join(faces) + _PDF_PAGE_CSS + "</style>"


def _pdf_link_callback(uri: str, rel: str) -> str:
    """Shablondagi rasm URL'larini (media/static) lokal fayl yo'liga aylantiradi."""
    if uri.startswith(("data:", "http://", "https://")) or os.path.isfile(uri):
        return uri
    relative = uri.lstrip("/")
    targets = (
        (settings.MEDIA_URL.lstrip("/"), (settings.MEDIA_ROOT,)),
        (
            settings.STATIC_URL.lstrip("/"),
            (getattr(settings, "STATIC_ROOT", None), Path(settings.BASE_DIR) / "static"),
        ),
    )
    for prefix, roots in targets:
        if prefix and relative.startswith(prefix):
            rest = relative[len(prefix):].lstrip("/")
            for root in roots:
                if root:
                    path = os.path.join(str(root), rest)
                    if os.path.isfile(path):
                        return path
    return uri


def html_to_pdf(html: str) -> bytes:
    # Bazaviy CSS <head> boshiga qo'yiladi — shablonning o'z stillari
    # keyin kelib, ustunlik qiladi (1:1 ko'rinish uchun).
    base_css = _build_pdf_base_css(html)
    match = _HEAD_TAG_RE.search(html)
    if match:
        html = html[: match.end()] + base_css + html[match.end():]
    else:
        html = base_css + html
    buffer = BytesIO()
    result = pisa.CreatePDF(src=html, dest=buffer, encoding="utf-8", link_callback=_pdf_link_callback)
    if result.err:
        raise ValueError("PDF generatsiya qilishda xatolik yuz berdi.")
    return buffer.getvalue()


# --- DOCX ---
# html4docx <head> ichidagi <style> blokini butunlay tashlab yuboradi va faqat
# inline style="" atributlarini o'qiydi. Shuning uchun DOCX'dan oldin CSS
# qoidalarini (cascade + meros bilan) elementlarga inline qilib singdiramiz.

def _parse_declarations(text: str) -> dict:
    decls = {}
    for part in text.split(";"):
        if ":" not in part:
            continue
        prop, value = part.split(":", 1)
        prop, value = prop.strip().lower(), value.strip()
        if prop and value:
            decls[prop] = value
    return decls


def _specificity(selector: str) -> tuple[int, int, int]:
    ids = selector.count("#")
    classes = selector.count(".") + selector.count("[") + selector.count(":")
    tags = len(re.findall(r"(?:^|[>+~\s])\s*([a-zA-Z][\w-]*)", selector))
    return ids, classes, tags


def _collect_css_rules(soup: BeautifulSoup) -> list:
    css = "\n".join(tag.get_text() for tag in soup.find_all("style"))
    css = _CSS_COMMENT_RE.sub("", css)
    css = _CSS_AT_BLOCK_RE.sub("", css)
    css = _CSS_AT_LINE_RE.sub("", css)
    rules = []
    for order, match in enumerate(_CSS_RULE_RE.finditer(css)):
        decls = _parse_declarations(match.group(2))
        if not decls:
            continue
        for selector in match.group(1).split(","):
            selector = selector.strip()
            if selector:
                rules.append((selector, _specificity(selector), order, decls))
    return rules


def _match_rules(soup: BeautifulSoup, rules: list) -> dict:
    matched: dict[int, list] = {}
    for selector, decls in _UA_DEFAULT_RULES:
        for el in soup.select(selector):
            matched.setdefault(id(el), []).append((((0, 0, 0), -1), decls))
    for selector, spec, order, decls in rules:
        try:
            selected = soup.select(selector)
        except Exception:
            continue
        for el in selected:
            matched.setdefault(id(el), []).append(((spec, order), decls))
    return matched


def _serialize_styles(styles: dict) -> str:
    return "; ".join(f"{prop}: {_IMPORTANT_RE.sub('', value)}" for prop, value in styles.items())


def _stamp_element(el, matched: dict, inherited: dict) -> dict:
    own = {}
    for _, decls in sorted(matched.get(id(el), []), key=lambda item: item[0]):
        own.update(decls)
    own.update(_parse_declarations(el.get("style", "")))
    computed = dict(inherited)
    computed.update(own)
    if computed:
        el["style"] = _serialize_styles(computed)
    next_inherited = {prop: value for prop, value in computed.items() if prop in _INHERITED_PROPS}
    # Katak ichidagi yalang'och matn alohida parser bilan o'qiladi va meros
    # stillarni yo'qotadi — uni style'li span bilan o'raymiz.
    if el.name in ("td", "th") and next_inherited:
        for child in list(el.children):
            if isinstance(child, NavigableString) and child.strip():
                span = BeautifulSoup("", "html.parser").new_tag("span")
                span["style"] = _serialize_styles(next_inherited)
                child.wrap(span)
    for child in el.find_all(recursive=False):
        _stamp_element(child, matched, next_inherited)
    return computed


def _inline_styles(soup: BeautifulSoup) -> dict:
    """CSS qoidalarini elementlarga inline qiladi, body'ning hisoblangan stilini qaytaradi."""
    rules = _collect_css_rules(soup)
    matched = _match_rules(soup, rules)
    for tag in soup.find_all(["style", "script", "link", "meta", "title"]):
        tag.decompose()
    root = soup.body or soup
    body_style = {}
    if soup.body is not None:
        body_style = _stamp_element(soup.body, matched, {})
        soup.body.attrs.pop("style", None)
    else:
        for child in root.find_all(recursive=False):
            _stamp_element(child, matched, {})
    return body_style


def _css_size_to_pt(value: str | None):
    if not value:
        return None
    match = _CSS_SIZE_RE.match(_IMPORTANT_RE.sub("", value).strip())
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2) or "px"
    factors = {"px": 0.75, "pt": 1.0, "em": 12.0, "rem": 12.0, "%": 0.12}
    factor = factors.get(unit)
    return Pt(round(number * factor, 1)) if factor else None


def _first_font_family(value: str | None):
    if not value:
        return None
    name = _IMPORTANT_RE.sub("", value).split(",")[0].strip().strip("'\"")
    if not name:
        return None
    return _GENERIC_FONT_MAP.get(name.lower(), name)


def _apply_document_defaults(document, body_style: dict) -> None:
    """PDF bilan bir xil sahifa (A4, 2cm) va bazaviy shriftni o'rnatadi."""
    section = document.sections[0]
    section.page_width, section.page_height = Cm(21.0), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2.0)
    section.left_margin = section.right_margin = Cm(2.0)

    font = document.styles["Normal"].font
    font.size = _css_size_to_pt(body_style.get("font-size")) or Pt(12)
    family = _first_font_family(body_style.get("font-family"))
    if family:
        font.name = family


def html_to_docx(html: str) -> bytes:
    soup = BeautifulSoup(html, "html.parser")
    body_style = _inline_styles(soup)
    document = HtmlToDocx().parse_html_string(str(soup))
    _apply_document_defaults(document, body_style)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
