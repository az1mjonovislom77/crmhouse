from django.urls import include, path
from rest_framework.routers import DefaultRouter
from client.views import ClientViewSet

router = DefaultRouter()
router.register('', ClientViewSet, basename='client')

urlpatterns = [
    path('', include(router.urls)),
]
