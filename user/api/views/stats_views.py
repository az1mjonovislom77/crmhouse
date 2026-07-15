from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user.selectors.user_selectors import get_user_stats


@extend_schema(tags=["UserStats"])
class UserStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = None if request.user.is_staff else request.user.organization
        stats = get_user_stats(organization=organization)

        return Response(stats, status=status.HTTP_200_OK)
