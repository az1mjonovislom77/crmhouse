from typing import Any


class AuditMixin:
    request: Any

    def perform_create(self, serializer):
        extra_kwargs: dict = {"created_by": self.request.user}

        model = serializer.Meta.model
        field_names = {f.name for f in model._meta.get_fields() if hasattr(f, "name")}
        if "user" in field_names:
            extra_kwargs["user"] = self.request.user
        if "organization" in field_names:
            extra_kwargs["organization"] = getattr(self.request.user, "organization", None)

        serializer.save(**extra_kwargs)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance._history_user = self.request.user
        instance.delete()
