from typing import Any


def get_user_org(request):
    if request.user.is_staff:
        return None
    return getattr(request.user, 'organization', None)


def filter_by_org(queryset, request, field='organization'):
    if request.user.is_staff:
        return queryset
    org = getattr(request.user, 'organization', None)
    if org is None:
        return queryset.none()
    return queryset.filter(**{field: org})


class OrganizationMixin:
    organization_field = 'organization'
    request: Any

    def get_queryset(self):
        qs = super().get_queryset()  # type: ignore[misc]
        return filter_by_org(qs, self.request, field=self.organization_field)
