from django.urls import path, include
from user.api.views.stats_views import UserStatsView
from rest_framework.routers import DefaultRouter
from user.api.views.auth_views import SignInAPIView, RefreshTokenAPIView, MeAPIView, LogOutAPIView
from user.api.views.user_views import UserViewSet
from user.api.views.log_views import RequestLogListView

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', SignInAPIView.as_view(), name='login'),
    path('logout/', LogOutAPIView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenAPIView.as_view(), name='token_refresh'),
    path('me/', MeAPIView.as_view(), name='me'),
    path('stats/', UserStatsView.as_view(), name='user_stats'),
    path('request-logs/', RequestLogListView.as_view(), name='request_logs'),
]
