from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from user.selectors.user_selectors import get_user_stats


@extend_schema(tags=["UserStats"])
class UserStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = get_user_stats()

        return Response(stats, status=status.HTTP_200_OK)
