from django.contrib import admin
from booking.models import Booking, PaymentTerm, Company


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'home']
    list_select_related = ['home', 'client']


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    list_display = ['id', 'months']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
