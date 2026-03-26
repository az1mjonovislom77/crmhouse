from django.urls import include, path
from rest_framework.routers import DefaultRouter
from utils.views import BlocksViewSet, FloorsViewSet, RenovationViewSet

router = DefaultRouter()
router.register('blocks', BlocksViewSet, basename='blocks')
router.register('floors', FloorsViewSet, basename='floors')
router.register('renovation', RenovationViewSet, basename='renovation')

urlpatterns = [
    path('', include(router.urls)),
]
