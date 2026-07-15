from django.db.models import Count, Prefetch, Q

from home.models import Home
from projects.models.showroom_models import Showroom, ShowroomImage


def get_showroom_images():
    showrooms = (
        Showroom.objects
        .select_related('block', 'block__projects')
        .annotate(
            homes_count=Count('block__homes'),
            available_homes=Count('block__homes', filter=Q(block__homes__home_status=Home.HomeStatus.AVAILABLE)),
            sold_homes=Count('block__homes', filter=Q(block__homes__home_status=Home.HomeStatus.SOLD)),
            reserved_homes=Count('block__homes', filter=Q(block__homes__home_status=Home.HomeStatus.RESERVED)))
    )
    return ShowroomImage.objects.prefetch_related(Prefetch('showrooms', queryset=showrooms))
