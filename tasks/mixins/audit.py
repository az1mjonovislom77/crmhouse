class AuditMixin:

    def perform_create(self, serializer):
        extra_kwargs = {"created_by": self.request.user}

        model = serializer.Meta.model
        if any(f.name == "user" for f in model._meta.get_fields() if hasattr(f, "name")):
            extra_kwargs["user"] = self.request.user

        serializer.save(**extra_kwargs)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance._history_user = self.request.user
        instance.delete()
