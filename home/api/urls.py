from django.urls import path, include
from rest_framework.routers import DefaultRouter
from home.api.views.home_views import HomeViewSet, HomeHistoryListAPIView

router = DefaultRouter()
router.register('home', HomeViewSet, basename='home')

urlpatterns = [
    path('', include(router.urls)),
    path("home-history/", HomeHistoryListAPIView.as_view()),

]
