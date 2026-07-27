from django.contrib import admin

from calculator.models import CalculatorConfig, GuaranteeOption, SubsidyOption


@admin.register(CalculatorConfig)
class CalculatorConfigAdmin(admin.ModelAdmin):
    list_display = ["__str__", "organization", "formula_key", "annual_rate_pct"]
    list_filter = ["formula_key"]


@admin.register(GuaranteeOption)
class GuaranteeOptionAdmin(admin.ModelAdmin):
    list_display = ["label", "organization", "key", "percent", "is_active", "order"]
    list_filter = ["organization"]


@admin.register(SubsidyOption)
class SubsidyOptionAdmin(admin.ModelAdmin):
    list_display = ["label", "organization", "key", "amount", "is_active", "order"]
    list_filter = ["organization"]
