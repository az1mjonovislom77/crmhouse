from django.db import models
from home.models import Home
from phonenumber_field.modelfields import PhoneNumberField


class PaymentTerm(models.Model):
    months = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.months} oy"


class Booking(models.Model):
    class DownPaymentChoice(models.IntegerChoices):
        TEN = 10, "10%"
        TWENTY = 20, "20%"
        THIRTY = 30, "30%"
        FORTY = 40, "40%"
        FIFTY = 50, "50%"

    home = models.OneToOneField(Home, on_delete=models.CASCADE, related_name="booking")
    full_name = models.CharField(max_length=100)
    phone_number = PhoneNumberField()
    passport = models.CharField(max_length=20)
    address = models.CharField(max_length=250)
    down_payment = models.IntegerField(choices=DownPaymentChoice.choices)
    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.full_name
