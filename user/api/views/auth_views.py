from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema
from user.services.auth.auth_service import AuthService
from user.services.auth.token_service import UserTokenService
from user.api.serializers.auth_serializers import SignInSerializer, LogoutSerializer, MeSerializer
from user.services.common.request_service import get_client_ip


@extend_schema(tags=["Auth"])
class SignInAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = SignInSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip = get_client_ip(request)

        result = AuthService.login_user(
            username=serializer.validated_data.get("username"),
            password=serializer.validated_data.get("password"),
            ip=ip
        )

        tokens = result["tokens"]

        response = Response(
            {
                "success": True,
                "message": "User logged in successfully",
                "data": {"access": tokens["access"]}
            }, status=status.HTTP_200_OK)

        UserTokenService.set_refresh_cookie(response, tokens["refresh"])

        return response


@extend_schema(tags=["Auth"])
class RefreshTokenAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request):
        refresh_token = request.COOKIES.get(UserTokenService.COOKIE_NAME)

        result = AuthService.refresh_user_token(refresh_token)

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Auth"])
class LogOutAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthService.logout_user(serializer.validated_data.get("refresh"))

        response = Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)

        UserTokenService.clear_refresh_cookie(response)
        return response


@extend_schema(tags=["Profile"])
class MeAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MeSerializer

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
