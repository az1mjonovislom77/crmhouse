from django.urls import path, include
from rest_framework.routers import DefaultRouter
from projects.api.views.project_views import ProjectViewSet, BlockViewSet, FloorsViewSet, RenovationViewSet
from projects.api.views.showroom_views import SVGView, ShowroomView

router = DefaultRouter()
router.register('projects', ProjectViewSet, basename='projects')
router.register('blocks', BlockViewSet, basename='blocks')
router.register('floors', FloorsViewSet, basename='floors')
router.register('renovation', RenovationViewSet, basename='renovation')

urlpatterns = [
    path('', include(router.urls)),
    path('svg/', SVGView.as_view()),
    path('showroom/', ShowroomView.as_view()),

]
