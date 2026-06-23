from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Client(models.Model):
    full_name = models.CharField(max_length=100)
    phone_number = PhoneNumberField()
    phone_number2 = PhoneNumberField(null=True, blank=True)
    passport = models.CharField(max_length=20)
    passport_date = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=500)

    def __str__(self):
        return self.full_name
