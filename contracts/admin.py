from django.contrib import admin

from contracts.models import Contract, ContractTemplate


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'organization']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['id', 'number', 'template', 'booking']
    list_select_related = ['template', 'booking']
