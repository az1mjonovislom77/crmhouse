from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

from client.models import Client
from common.services.numbers import number_to_words_uz
from home.models import Home


class Company(models.Model):
    organization = models.ForeignKey(
        "organization.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="companies"
    )
    name = models.CharField(max_length=250)
    address = models.CharField(max_length=250)
    phone = models.CharField(max_length=250)
    hr = models.CharField(max_length=250, null=True, blank=True)
    mfo = models.CharField(max_length=250, null=True, blank=True)
    inn = models.CharField(max_length=250, null=True, blank=True)
    bank = models.CharField(max_length=250, null=True, blank=True)
    director_name = models.CharField(max_length=250, null=True, blank=True)
    director_short_name = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.name


class Booking(models.Model):
    class PaymentType(models.TextChoices):
        BOSH_TOLOVLI = "bosh_tolovli", "Bosh to`lovli"
        BOSH_TOLOVSIZ = "bosh_tolovsiz", "Bosh to`lovsiz"

    class BookingStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        CANCELED = "canceled", "Canceled"

    organization = models.ForeignKey(
        "organization.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings"
    )
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name="bookings")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bookings")
    description = models.TextField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    map_key = models.CharField(max_length=200, null=True, blank=True)
    booking_no = models.CharField(max_length=200, null=True, blank=True)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices, null=True, blank=True)
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.ACTIVE, db_index=True)
    price_per_m2 = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    guarantee_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    credit_years = models.PositiveIntegerField(null=True, blank=True)
    manual_down_payment = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
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
    payment_start_date = models.DateField(null=True, blank=True)
    payment_end_date = models.DateField(null=True, blank=True)
    ownership_deadline = models.DateField(null=True, blank=True)
    registration_workdays = models.PositiveIntegerField(null=True, blank=True)
    monthly_payment_day = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["home"],
                condition=models.Q(status="active"),
                name="unique_active_booking_per_home",
            ),
        ]

    def __str__(self):
        return str(self.id)

    @property
    def total_price(self):
        if self.contract_price:
            return self.contract_price
        total = (self.home.price_per_sqm or 0) * (self.home.area or 0)
        if self.home.renovation:
            total += self.home.renovation.price
        return total

    @property
    def total_price_inword(self):
        return number_to_words_uz(self.total_price)

    @property
    def manual_down_payment_inword(self):
        return number_to_words_uz(self.manual_down_payment)

    @property
    def client_payment_inword(self):
        return number_to_words_uz(self.client_payment)

    def paid_total(self):
        if hasattr(self, "payments_total"):
            return self.payments_total or 0
        return self.payments.aggregate(total=Sum("amount"))["total"] or 0

    @property
    def remaining_debt(self):
        return self.total_price - self.paid_total()

    @property
    def total_planned(self):
        from booking.services.schedule import total_planned

        return total_planned(self)

    @property
    def payable_remaining(self):
        planned = self.total_planned
        if planned is None:
            return self.remaining_debt
        return planned - self.paid_total()


class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    file = models.FileField(
        upload_to="payments/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png", "webp"])],
    )
    payment_date = models.DateField(default=timezone.localdate, null=True, blank=True)
    payment_data = models.TextField(null=True, blank=True)
    payment_number = models.CharField(max_length=200, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.id} - {self.amount}"


class Commitment(models.Model):
    class CommitmentStatus(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        FULFILLED = "fulfilled", "Bajarildi"
        BROKEN = "broken", "Buzildi"

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="commitments")
    expected_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    note = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=CommitmentStatus.choices, default=CommitmentStatus.PENDING, db_index=True
    )
    reminder = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="commitments"
    )

    class Meta:
        ordering = ["expected_date", "id"]

    def __str__(self):
        return f"Commitment {self.id} - {self.amount} ({self.expected_date})"


@receiver(post_delete, sender=Payment)
def delete_payment_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
