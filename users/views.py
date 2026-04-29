from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import AuditLog
from .utils import log_action
from .serializers import (
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    RegisterSerializer,
    SubAccountCreateSerializer,
    TEAM_MAX_SUB_ACCOUNTS,
    UserSerializer,
    AuditLogSerializer,
    ensure_user_profile,
)


class AuditLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ensure_user_profile(request.user)
        logs = AuditLog.objects.filter(team=profile.team).select_related("user").all()[:100]
        return Response(AuditLogSerializer(logs, many=True).data)



class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"user": UserSerializer(user).data}, status=201)


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
        subaccount_count = profile.team.members.filter(role="MEMBER").count()
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "team": {
                    "code": profile.team.code,
                    "name": profile.team.name,
                    "max_subaccounts": TEAM_MAX_SUB_ACCOUNTS,
                    "current_subaccounts": subaccount_count,
                },
                "is_team_admin": profile.team.admin_user_id == request.user.id,
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

    def delete(self, request):
        profile = ensure_user_profile(request.user)
        if profile.team.admin_user_id != request.user.id:
            return Response({"detail": "只有管理员可以删除账号。"}, status=403)

        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "缺少 user_id。"}, status=400)
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return Response({"detail": "user_id 格式不正确。"}, status=400)

        members = profile.team.members.select_related("user").all()
        user_map = {m.user.id: m for m in members}
        target = user_map.get(user_id)
        if not target:
            return Response({"detail": "账号不存在或不属于当前团队。"}, status=404)

        if target.user.id == request.user.id:
            return Response({"detail": "不能删除自己。"}, status=400)

        if profile.team.admin_user_id == target.user.id:
            return Response({"detail": "不能删除管理员账号。"}, status=400)

        username = target.user.username
        target.user.delete()
        log_action(
            user=request.user,
            action="DELETE",
            resource="账号",
            description=f"删除成员账号：{username}",
            request=request,
        )
        return Response(status=204)
