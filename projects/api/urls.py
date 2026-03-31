from django.urls import path, include
from rest_framework.routers import DefaultRouter
from projects.api.views.project_views import ProjectsViewSet, BlocksViewSet, FloorsViewSet, RenovationViewSet
from projects.api.views.showroom_views import SVGView

router = DefaultRouter()
router.register('projects', ProjectsViewSet, basename='projects')
router.register('blocks', BlocksViewSet, basename='blocks')
router.register('floors', FloorsViewSet, basename='floors')
router.register('renovation', RenovationViewSet, basename='renovation')

urlpatterns = [
    path('', include(router.urls)),
    path('svg/', SVGView.as_view()),

]
