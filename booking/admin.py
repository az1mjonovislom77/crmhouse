from django.contrib import admin

from booking.models import Booking, Company, Payment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'home']
    list_select_related = ['home', 'client']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'inn', 'mfo', 'bank', 'director_name']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'amount', 'note']
