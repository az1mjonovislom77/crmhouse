from django.urls import path
from .views import InstagramViewSet

media_view = InstagramViewSet.as_view({"get": "media"})
comments_view = InstagramViewSet.as_view({"get": "comments"})
reply_view = InstagramViewSet.as_view({"post": "reply"})

urlpatterns = [
    path("media/", media_view),
    path("comments/", comments_view),
    path("reply/", reply_view),
]
