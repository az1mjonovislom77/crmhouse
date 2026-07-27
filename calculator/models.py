from django.db import models


def default_term_options():
    return [20, 15]


class CalculatorConfig(models.Model):
    class Formula(models.TextChoices):
        STANDART = "standart", "Standart (annuitet)"
        TENG_ULUSH = "teng_ulush", "Teng ulush (foizsiz)"

    organization = models.OneToOneField(
        "organization.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="calculator_config"
    )
    formula_key = models.CharField(max_length=30, choices=Formula.choices, default=Formula.STANDART)

    annual_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, default=17)
    state_threshold_pct = models.DecimalField(max_digits=5, decimal_places=2, default=14)
    subsidy_years = models.PositiveIntegerField(default=5)
    firm_markup_pct = models.DecimalField(max_digits=5, decimal_places=2, default=16)
    round_step = models.PositiveIntegerField(default=1000)
    default_price_per_m2 = models.DecimalField(max_digits=14, decimal_places=2, default=7700000)
    term_options = models.JSONField(default=default_term_options)

    def __str__(self):
        return f"Config ({self.organization or 'global'})"

    _COPY_FIELDS = [
        "formula_key",
        "annual_rate_pct",
        "state_threshold_pct",
        "subsidy_years",
        "firm_markup_pct",
        "round_step",
        "default_price_per_m2",
        "term_options",
    ]

    @classmethod
    def for_org(cls, organization=None):
        obj = cls.objects.filter(organization=organization).first()
        if obj is None and organization is not None:
            obj = cls.objects.filter(organization__isnull=True).first()
        if obj is None:
            obj = cls.objects.create(organization=None)
        return obj

    @classmethod
    def resolve_for_edit(cls, organization=None):
        obj = cls.objects.filter(organization=organization).first()
        if obj is not None:
            return obj
        base = cls.objects.filter(organization__isnull=True).first()
        defaults = {f: getattr(base, f) for f in cls._COPY_FIELDS} if base else {}
        return cls.objects.create(organization=organization, **defaults)

    @classmethod
    def load(cls):
        return cls.for_org(None)


class GuaranteeOption(models.Model):
    organization = models.ForeignKey(
        "organization.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="guarantee_options"
    )
    key = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("organization", "key")]

    def __str__(self):
        return self.label


class SubsidyOption(models.Model):
    organization = models.ForeignKey(
        "organization.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="subsidy_options"
    )
    key = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("organization", "key")]

    def __str__(self):
        return self.label


def options_for(model, organization=None):
    qs = model.objects.filter(organization=organization)
    if organization is not None and not qs.exists():
        qs = model.objects.filter(organization__isnull=True)
    return qs


def materialize_org_options(model, organization):
    if organization is None or model.objects.filter(organization=organization).exists():
        return
    field_names = [f.name for f in model._meta.concrete_fields if f.name not in ("id", "organization")]
    copies = [
        model(organization=organization, **{name: getattr(base, name) for name in field_names})
        for base in model.objects.filter(organization__isnull=True)
    ]
    model.objects.bulk_create(copies)


def active_guarantees(organization=None):
    qs = GuaranteeOption.objects.filter(organization=organization, is_active=True)
    if organization is not None and not qs.exists():
        qs = GuaranteeOption.objects.filter(organization__isnull=True, is_active=True)
    return qs


def active_subsidies(organization=None):
    qs = SubsidyOption.objects.filter(organization=organization, is_active=True)
    if organization is not None and not qs.exists():
        qs = SubsidyOption.objects.filter(organization__isnull=True, is_active=True)
    return qs
