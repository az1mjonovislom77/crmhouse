from django.contrib import admin

from booking.models import Booking, PaymentTerm


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'home']


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    list_display = ['id', 'months']
