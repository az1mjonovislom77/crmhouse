from django.urls import path, include
from rest_framework.routers import DefaultRouter

from projects.views import ProjectsViewSet

router = DefaultRouter()
router.register('projects', ProjectsViewSet, basename='projects')

urlpatterns = [
    path('', include(router.urls)),

]
