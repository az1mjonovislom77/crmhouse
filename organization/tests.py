import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from booking.models import Booking
from common.factories import make_blocks, make_client, make_company, make_home, make_project, make_user
from organization.models import Organization
from tasks.models import Card

TEMP_MEDIA = tempfile.mkdtemp()


def make_png_upload(name="logo.png", size=(10, 10)):
    buffer = BytesIO()
    Image.new("RGB", size, color="red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class OrganizationModelTest(TestCase):
    def test_str_returns_name(self):
        org = Organization.objects.create(name="ATS Systems")
        self.assertEqual(str(org), "ATS Systems")

    def test_logo_converted_to_webp_on_create(self):
        org = Organization.objects.create(name="Webp Org", logo=make_png_upload())
        self.assertTrue(org.logo.name.lower().endswith(".webp"))

    def test_unchanged_logo_not_reprocessed_on_update(self):
        org = Organization.objects.create(name="Stable Org", logo=make_png_upload())
        name_after_create = org.logo.name
        org.is_active = False
        org.save()
        org.refresh_from_db()
        self.assertEqual(org.logo.name, name_after_create)
        self.assertFalse(org.is_active)

    def test_save_without_logo(self):
        org = Organization.objects.create(name="No Logo Org")
        self.assertFalse(org.logo)


class BackfillOrganizationsCommandTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Backfill Org")
        self.user = make_user(username="backfill_user", organization=self.org)

    def test_backfills_from_related_chain(self):
        project = make_project(user=self.user)
        block = make_blocks(projects=project)
        home = make_home(blocks=block)
        booking = Booking.objects.create(home=home, client=make_client(), company=make_company())
        card = Card.objects.create(title="Card 1", created_by=self.user)

        call_command("backfill_organizations", verbosity=0)

        project.refresh_from_db()
        home.refresh_from_db()
        booking.refresh_from_db()
        card.refresh_from_db()
        self.assertEqual(project.organization_id, self.org.pk)
        self.assertEqual(home.organization_id, self.org.pk)
        self.assertEqual(booking.organization_id, self.org.pk)
        self.assertEqual(card.organization_id, self.org.pk)

    def test_rows_without_chain_stay_empty(self):
        orphan_user = make_user(username="orphan_user", organization=None)
        project = make_project(user=orphan_user)
        card = Card.objects.create(title="Card 2", created_by=orphan_user)

        call_command("backfill_organizations", verbosity=0)

        project.refresh_from_db()
        card.refresh_from_db()
        self.assertIsNone(project.organization_id)
        self.assertIsNone(card.organization_id)

    def test_existing_organization_not_overwritten(self):
        other_org = Organization.objects.create(name="Other Org")
        project = make_project(user=self.user, organization=other_org)

        call_command("backfill_organizations", verbosity=0)

        project.refresh_from_db()
        self.assertEqual(project.organization_id, other_org.pk)
