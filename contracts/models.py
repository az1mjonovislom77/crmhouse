from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

from booking.models import Booking

MONTH_NAMES_UZ = (
    "yanvar", "fevral", "mart", "aprel", "may", "iyun",
    "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr",
)


class ContractTemplate(models.Model):
    organization = models.ForeignKey(
        'organization.Organization', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='contract_templates')
    name = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='contracts/templates/',
        validators=[FileExtensionValidator(allowed_extensions=['html', 'htm'])])
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def read_html(self) -> str:
        with self.file.open('rb') as f:
            return f.read().decode('utf-8')


class Contract(models.Model):
    organization = models.ForeignKey(
        'organization.Organization', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='contracts')
    template = models.ForeignKey(ContractTemplate, on_delete=models.PROTECT, related_name='contracts')
    booking = models.ForeignKey(
        Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts')
    number = models.CharField(max_length=200, null=True, blank=True)
    contract_date = models.DateField(null=True, blank=True)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.number or str(self.id)

    def save(self, *args, **kwargs):
        if not self.number and self.booking and self.booking.home:
            home = self.booking.home
            if home.blocks:
                self.number = f"{home.blocks.title}/{home.home_number}"
            else:
                self.number = str(home.home_number)
        super().save(*args, **kwargs)

    @property
    def contract_date_uz(self):
        if not self.contract_date:
            return ""
        d = self.contract_date
        return f"{d.year}-yil “{d.day:02d}”-{MONTH_NAMES_UZ[d.month - 1]}"


@receiver(post_delete, sender=ContractTemplate)
def delete_template_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
