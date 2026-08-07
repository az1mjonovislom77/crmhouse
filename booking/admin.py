from django.contrib import admin

from booking.models import Booking, Commitment, Company, Payment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "home"]
    list_select_related = ["home", "client"]


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "inn", "mfo", "bank", "director_name"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "amount", "note"]


@admin.register(Commitment)
class CommitmentAdmin(admin.ModelAdmin):
    list_display = ["id", "booking", "expected_date", "amount", "status", "reminder"]
    list_filter = ["status", "reminder"]
    list_select_related = ["booking"]
