from rest_framework import serializers


class BaseReadSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        fields = "__all__"
