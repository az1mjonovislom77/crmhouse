from drf_spectacular.utils import extend_schema
from django.db.models import Case, When, Value, ExpressionWrapper, FloatField, F
from home.models import Home
from projects.models import Projects
from projects.serializers import ProjectsSerializer
from utils.base.views_base import BaseUserViewSet
from django.db.models import Count, Q


@extend_schema(tags=['Projects'])
class ProjectsViewSet(BaseUserViewSet):
    serializer_class = ProjectsSerializer

    def get_queryset(self):
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
                    filter=Q(blocks__homes__home_status=Home.HomeStatus.SOLD), distinct=True))
            .annotate(
                sold_percent=Case(
                    When(homes_count=0, then=Value(0.0)),
                    default=ExpressionWrapper(100.0 * F('sold_homes') / F('homes_count'), output_field=FloatField()),
                    output_field=FloatField())))
