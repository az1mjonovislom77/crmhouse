from django.db.models import Count, Q
from user.models import User


class UserStatsService:

    @staticmethod
    def dashboard():
        stats = User.objects.aggregate(
            total_users=Count("id"),
            total_salers=Count("id", filter=Q(role=User.UserRoles.SELLER)),
            total_admins=Count("id", filter=Q(role__in=[User.UserRoles.MANAGER]))
        )

        return stats
