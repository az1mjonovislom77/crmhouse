from django.urls import path, include
from rest_framework.routers import DefaultRouter
from home.views import HomeViewSet

router = DefaultRouter()
router.register('home', HomeViewSet, basename='home')

urlpatterns = [
    path('', include(router.urls)),

]
