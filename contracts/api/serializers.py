from rest_framework import serializers

from contracts.models import Contract, ContractTemplate


class ContractTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractTemplate
        fields = ["id", "name", "file", "created_at"]


class ContractSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)

    class Meta:
        model = Contract
        fields = ["id", "template", "template_name", "booking", "number", "contract_date", "data", "created_at"]
