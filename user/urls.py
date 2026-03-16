from django.urls import path, include
from user.views.stats_views import UserStatsView
from user.views.user_views import UserViewSet
from rest_framework.routers import DefaultRouter
from user.views.auth_views import SignInAPIView, RefreshTokenAPIView, MeAPIView, LogOutAPIView

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', SignInAPIView.as_view(), name='login'),
    path('logout/', LogOutAPIView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenAPIView.as_view(), name='token_refresh'),
    path('me/', MeAPIView.as_view(), name='me'),
    path('stats/users/', UserStatsView.as_view(), name='user_stats')
]
