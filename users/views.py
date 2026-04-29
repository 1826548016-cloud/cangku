from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    SubAccountCreateSerializer,
    TEAM_MAX_SUB_ACCOUNTS,
    UserSerializer,
    ensure_user_profile,
)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenRefreshSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ensure_user_profile(request.user)
        subaccount_count = profile.team.members.filter(user__is_superuser=False).count()
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "team": {
                    "code": profile.team.code,
                    "name": profile.team.name,
                    "max_subaccounts": TEAM_MAX_SUB_ACCOUNTS,
                    "current_subaccounts": subaccount_count,
                },
            }
        )


class TeamSubAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ensure_user_profile(request.user)
        members = profile.team.members.select_related("user").all()
        users = [item.user for item in members]
        return Response(
            {
                "team_code": profile.team.code,
                "max_subaccounts": TEAM_MAX_SUB_ACCOUNTS,
                "members": UserSerializer(users, many=True).data,
            }
        )

    def post(self, request):
        serializer = SubAccountCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"user": UserSerializer(user).data}, status=201)
