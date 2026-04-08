from django.db import models
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
        TEN = 10, "10%"
        TWENTY = 20, "20%"
        THIRTY = 30, "30%"
        FORTY = 40, "40%"
        FIFTY = 50, "50%"

    home = models.OneToOneField(Home, on_delete=models.CASCADE, related_name="booking")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bookings")
    cash_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    down_payment = models.IntegerField(choices=DownPaymentChoice.choices)
    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)
