import tempfile
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from booking.models import Booking
from common.factories import make_blocks, make_client, make_company, make_home, make_user
from contracts.models import Contract, ContractTemplate
from contracts.services.render import (
    BlankNoneWrapper,
    build_context,
    extract_placeholders,
    html_to_docx,
    html_to_pdf,
    render_contract_html,
)

TEMP_MEDIA = tempfile.mkdtemp()

TEMPLATE_HTML = (
    "<html><head><title>Shartnoma</title></head>"
    "<body><h1>{{ client.full_name }}</h1>"
    "<p>Narx: {{ total_price }} ({{ total_price_sozda }})</p>"
    "<p>Sana: {{ contract.contract_date_uz }}</p></body></html>"
)


def make_template(**kwargs):
    defaults = {
        "name": "Asosiy shablon",
        "file": SimpleUploadedFile("shablon.html", TEMPLATE_HTML.encode("utf-8"), content_type="text/html"),
    }
    defaults.update(kwargs)
    return ContractTemplate.objects.create(**defaults)


def make_booking(**kwargs):
    defaults = {
        "home": kwargs.pop("home", None) or make_home(),
        "client": kwargs.pop("client", None) or make_client(),
        "company": kwargs.pop("company", None) or make_company(),
    }
    defaults.update(kwargs)
    return Booking.objects.create(**defaults)


class ExtractPlaceholdersTest(TestCase):
    def test_finds_unique_sorted_placeholders(self):
        html = "{{ b }} {{a}} {{ b }} {{ client.full_name }}"
        self.assertEqual(extract_placeholders(html), ["a", "b", "client.full_name"])

    def test_no_placeholders(self):
        self.assertEqual(extract_placeholders("<p>oddiy matn</p>"), [])


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ContractModelTest(TestCase):
    def test_number_auto_set_from_block_and_home(self):
        home = make_home(blocks=make_blocks(title="A blok"), home_number=7)
        contract = Contract.objects.create(template=make_template(), booking=make_booking(home=home))
        self.assertEqual(contract.number, "A blok/7")

    def test_number_auto_set_without_block(self):
        home = make_home(home_number=9)
        contract = Contract.objects.create(template=make_template(), booking=make_booking(home=home))
        self.assertEqual(contract.number, "9")

    def test_explicit_number_not_overwritten(self):
        contract = Contract.objects.create(template=make_template(), booking=make_booking(), number="X-1")
        self.assertEqual(contract.number, "X-1")

    def test_contract_date_uz_formatting(self):
        contract = Contract.objects.create(template=make_template(), contract_date=date(2026, 7, 5))
        self.assertEqual(contract.contract_date_uz, "2026-yil “05”-iyul")

    def test_contract_date_uz_empty_when_no_date(self):
        contract = Contract.objects.create(template=make_template())
        self.assertEqual(contract.contract_date_uz, "")


class BlankNoneWrapperTest(TestCase):
    def test_none_attribute_becomes_empty_string(self):
        wrapped = BlankNoneWrapper(make_client())
        self.assertEqual(wrapped.full_name, "Test Client")

    def test_nested_model_is_wrapped(self):
        booking = make_booking()
        wrapped = BlankNoneWrapper(booking)
        self.assertIsInstance(wrapped.client, BlankNoneWrapper)
        self.assertEqual(wrapped.description, "")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class BuildContextTest(TestCase):
    def test_booking_keys_present(self):
        booking = make_booking(contract_price=379995000)
        contract = Contract.objects.create(template=make_template(), booking=booking)
        ctx = build_context(contract)
        for key in ("booking", "client", "home", "company", "total_price", "total_price_sozda", "contract"):
            self.assertIn(key, ctx)

    def test_data_numbers_get_sozda_variant(self):
        contract = Contract.objects.create(template=make_template(), data={"avans": "1000"})
        ctx = build_context(contract)
        self.assertEqual(ctx["avans_sozda"], "ming")

    def test_data_overrides_are_kept(self):
        booking = make_booking()
        contract = Contract.objects.create(template=make_template(), booking=booking, data={"total_price": "5000"})
        ctx = build_context(contract)
        self.assertEqual(ctx["total_price"], "5000")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class RenderContractTest(TestCase):
    def setUp(self):
        self.booking = make_booking(contract_price=1000000)
        self.contract = Contract.objects.create(
            template=make_template(), booking=self.booking, contract_date=date(2026, 1, 15)
        )

    def test_render_html_substitutes_values(self):
        html = render_contract_html(self.contract)
        self.assertIn("Test Client", html)
        self.assertIn("1000000", html)
        self.assertIn("bir million", html)
        self.assertIn("2026-yil", html)

    def test_html_to_pdf_returns_pdf_bytes(self):
        pdf = html_to_pdf(render_contract_html(self.contract))
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_html_to_docx_returns_docx_bytes(self):
        docx = html_to_docx(render_contract_html(self.contract))
        self.assertTrue(docx.startswith(b"PK"))


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ContractApiTest(APITestCase):
    def setUp(self):
        self.user = make_user(username="contract_admin")
        self.client.force_authenticate(self.user)
        self.template = make_template()
        self.contract = Contract.objects.create(
            template=self.template, booking=make_booking(), contract_date=date(2026, 3, 1)
        )

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse("contract-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_contracts(self):
        response = self.client.get(reverse("contract-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_preview_returns_rendered_html(self):
        response = self.client.get(reverse("contract-preview", args=[self.contract.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Test Client", response.content.decode("utf-8"))

    def test_download_pdf(self):
        response = self.client.get(reverse("contract-download", args=[self.contract.pk]), {"file_format": "pdf"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_download_docx(self):
        response = self.client.get(reverse("contract-download", args=[self.contract.pk]), {"file_format": "docx"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.content.startswith(b"PK"))

    def test_download_invalid_format_rejected(self):
        response = self.client.get(reverse("contract-download", args=[self.contract.pk]), {"file_format": "exe"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_template_placeholders_action(self):
        response = self.client.get(reverse("contract-template-placeholders", args=[self.template.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("client.full_name", response.data["placeholders"])
