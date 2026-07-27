from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tasks.api.views import CardViewSet, CommentViewSet, ProjectViewSet

router = DefaultRouter()
router.register("card", CardViewSet, basename="card")
router.register("comment", CommentViewSet, basename="comment")
router.register("project", ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
]
