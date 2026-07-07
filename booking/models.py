from django.db import models
from django.db.models import Sum
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from home.models import Home
from client.models import Client


class Company(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Booking(models.Model):
    class PaymentType(models.TextChoices):
        BOSH_TOLOVLI = 'bosh_tolovli', 'Bosh to`lovli'
        BOSH_TOLOVSIZ = 'bosh_tolovsiz', 'Bosh to`lovsiz'

    home = models.OneToOneField(Home, on_delete=models.CASCADE, related_name="booking")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bookings")
    description = models.TextField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    map_key = models.CharField(max_length=200, null=True, blank=True)
    booking_no = models.CharField(max_length=200, null=True, blank=True)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices, null=True, blank=True)
    price_per_m2 = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    guarantee_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    credit_years = models.PositiveIntegerField(null=True, blank=True)
    manual_down_payment = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    rounding = models.BooleanField(default=True)
    annual_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    state_threshold_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    subsidy_years = models.PositiveIntegerField(null=True, blank=True)
    firm_markup_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    contract_price = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    firm_covers = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    client_payment = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    subsidy_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    monthly_full = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    monthly_stage1 = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    gov_monthly = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    @property
    def total_price(self):
        total = (self.home.price_per_sqm or 0) * (self.home.area or 0)
        if self.home.renovation:
            total += self.home.renovation.price
        return total

    @property
    def remaining_debt(self):
        if hasattr(self, 'payments_total'):
            paid = self.payments_total or 0
        else:
            paid = self.payments.aggregate(total=Sum('amount'))['total'] or 0
        return self.total_price - paid

    def __str__(self):
        return str(self.id)


class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    file = models.FileField(
        upload_to='payments/', null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'webp'])]
    )
    payment_date = models.DateField(default=timezone.localdate, null=True, blank=True)
    payment_data = models.TextField(null=True, blank=True)
    payment_number = models.CharField(max_length=200, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.id} - {self.amount}"


@receiver(post_delete, sender=Payment)
def delete_payment_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
