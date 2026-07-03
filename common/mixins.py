def get_user_org(request):
    """Returns user's organization, or None for Django staff/superusers."""
    if request.user.is_staff:
        return None
    return getattr(request.user, 'organization', None)


def filter_by_org(queryset, request, field='organization'):
    """Filters queryset to the current user's organization. Staff sees everything.
    Non-staff users without an organization see nothing (fail closed)."""
    if request.user.is_staff:
        return queryset
    org = getattr(request.user, 'organization', None)
    if org is None:
        return queryset.none()
    return queryset.filter(**{field: org})


class OrganizationMixin:
    """
    Mixin for ViewSets whose model has a direct 'organization' FK.
    Override organization_field for related lookups (e.g. 'card__organization').
    """
    organization_field = 'organization'

    def get_queryset(self):
        qs = super().get_queryset()
        return filter_by_org(qs, self.request, field=self.organization_field)
