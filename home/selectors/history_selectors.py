from home.models import HomeStatusHistory


def get_home_history(home_id, user_id=None):
    qs = HomeStatusHistory.objects.select_related("home", "home__blocks", "home__floor", "changed_by").filter(home_id=home_id)

    if user_id:
        qs = qs.filter(changed_by_id=user_id)

    return qs.order_by("-changed_at")
