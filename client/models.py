from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Client(models.Model):
    full_name = models.CharField(max_length=100)
    phone_number = PhoneNumberField()
    passport = models.CharField(max_length=20)
    address = models.CharField(max_length=250)

    def __str__(self):
        return self.full_name
