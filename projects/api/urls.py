from django.urls import path, include
from rest_framework.routers import DefaultRouter
from projects.api.views import ProjectsViewSet, BlocksViewSet, FloorsViewSet, RenovationViewSet

router = DefaultRouter()
router.register('projects', ProjectsViewSet, basename='projects')
router.register('blocks', BlocksViewSet, basename='blocks')
router.register('floors', FloorsViewSet, basename='floors')
router.register('renovation', RenovationViewSet, basename='renovation')

urlpatterns = [
    path('', include(router.urls)),

]
