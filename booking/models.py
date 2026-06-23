from django.db import models
from django.db.models import Sum
from django.utils import timezone
from home.models import Home
from client.models import Client


class PaymentTerm(models.Model):
    months = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.months} oy"


class Company(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Booking(models.Model):
    class DownPaymentChoice(models.IntegerChoices):
        ZERO = 0, '0'
        TEN = 10, "10%"
        TWENTY = 20, "20%"
        THIRTY = 30, "30%"
        FORTY = 40, "40%"
        FIFTY = 50, "50%"

    home = models.OneToOneField(Home, on_delete=models.CASCADE, related_name="booking")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bookings")
    cash_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    down_payment = models.IntegerField(choices=DownPaymentChoice.choices, null=True, blank=True)
    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    map_key = models.CharField(max_length=200, null=True, blank=True)
    booking_no = models.CharField(max_length=200, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    @property
    def total_price(self):
        return self.home.price_per_sqm * self.home.area

    @property
    def remaining_debt(self):
        down_payment_amount = (self.total_price * self.down_payment / 100) if self.down_payment else 0
        if hasattr(self, 'payments_total'):
            paid = self.payments_total or 0
        else:
            paid = self.payments.aggregate(total=Sum('amount'))['total'] or 0
        return self.total_price - self.cash_payment - down_payment_amount - paid

    def __str__(self):
        return str(self.id)


class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.id} - {self.amount}"
