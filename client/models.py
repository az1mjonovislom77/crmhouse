from django.conf import settings
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Client(models.Model):
    full_name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = PhoneNumberField()
    phone_number2 = PhoneNumberField(null=True, blank=True)
    passport = models.CharField(max_length=20)
    passport_date = models.DateField(null=True, blank=True)
    jshshir = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=500)
    from_who = models.CharField(max_length=200, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="clients"
    )
    organization = models.ForeignKey(
        "organization.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="clients"
    )

    def __str__(self):
        return self.full_name
