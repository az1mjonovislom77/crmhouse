from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .serializers import CommentQuerySerializer, ReplySerializer
from .services import InstagramService, InstagramAPIError

instagram_service = InstagramService()

IG_USER_ID = "17841439835654723"


@extend_schema(tags=["Instagram"])
class InstagramViewSet(ViewSet):

    def media(self, request):
        try:
            data = instagram_service.get_media(IG_USER_ID)
            return Response(data)

        except InstagramAPIError as e:
            return Response({"error": str(e)}, status=400)

    @extend_schema(parameters=[CommentQuerySerializer], responses=dict)
    def comments(self, request):
        serializer = CommentQuerySerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        media_id = serializer.validated_data["media_id"]

        try:
            data = instagram_service.get_comments(media_id)
            return Response(data)

        except InstagramAPIError as e:
            return Response({"error": str(e)}, status=400)

    @extend_schema(request=ReplySerializer, responses=dict)
    def reply(self, request):
        serializer = ReplySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        comment_id = serializer.validated_data["comment_id"]
        message = serializer.validated_data["message"]

        try:
            data = instagram_service.reply_to_comment(comment_id, message)
            return Response(data)

        except InstagramAPIError as e:
            return Response({"error": str(e)}, status=400)
