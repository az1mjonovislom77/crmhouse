from django.db.models import Case, When, Value, ExpressionWrapper, FloatField, F, Count, Q
from home.models import Home
from projects.models.project_models import Projects


def get_projects_with_stats():
    return (
        Projects.objects
        .select_related('user')
        .prefetch_related('blocks')
        .annotate(
            homes_count=Count('blocks__homes', distinct=True),
            available_homes=Count(
                'blocks__homes',
                filter=Q(blocks__homes__home_status=Home.HomeStatus.AVAILABLE), distinct=True),
            sold_homes=Count(
                'blocks__homes',
                filter=Q(blocks__homes__home_status=Home.HomeStatus.SOLD), distinct=True)
        )
        .annotate(
            sold_percent=Case(
                When(homes_count=0, then=Value(0.0)),
                default=ExpressionWrapper(
                    100.0 * F('sold_homes') / F('homes_count'),
                    output_field=FloatField()), output_field=FloatField())))
