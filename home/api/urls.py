from django.urls import include, path
from rest_framework.routers import DefaultRouter

from home.api.home_views import HomeHistoryListAPIView, HomeViewSet

router = DefaultRouter()
router.register('home', HomeViewSet, basename='home')

urlpatterns = [
    path('', include(router.urls)),
    path("home-history/", HomeHistoryListAPIView.as_view()),

]
