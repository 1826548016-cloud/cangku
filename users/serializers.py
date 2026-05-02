from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.utils import OperationalError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Team, UserProfile, UserSession, AuditLog
from .utils import log_action

TEAM_MAX_SUB_ACCOUNTS = 3


def get_default_team():
    team, _ = Team.objects.get_or_create(code="TEAM001", defaults={"name": "默认团队"})
    return team


def ensure_user_profile(user):
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={"team": get_default_team(), "role": "MEMBER"}
    )
    return profile


class UserSerializer(serializers.ModelSerializer):
    team_code = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "is_superuser", "is_staff", "team_code", "team_name", "role", "date_joined"]

    def get_team_code(self, obj):
        return ensure_user_profile(obj).team.code

    def get_team_name(self, obj):
        return ensure_user_profile(obj).team.name

    def get_role(self, obj):
        profile = ensure_user_profile(obj)
        return "ADMIN" if profile.team.admin_user_id == obj.id else "MEMBER"


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "username", "action", "action_display", "resource", "description", "ip_address", "created_at"]



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    team_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        session_state, _ = UserSession.objects.get_or_create(user=user)
        token["session_version"] = session_state.session_version
        return token

    @transaction.atomic
    def validate(self, attrs):
        team_code = attrs.get("team_code")
        username = attrs.get("username")
        password = attrs.get("password")
        
        if not team_code:
            raise serializers.ValidationError({"team_code": ["该字段是必填项。"]})

        try:
            # 1. 验证团队是否存在
            team = Team.objects.get(code=team_code)
        except Team.DoesNotExist:
            raise serializers.ValidationError({"detail": "团队号不存在。"})
        except OperationalError:
            raise serializers.ValidationError({"detail": "数据库连接失败，请确认 MySQL 服务已启动。"})

        try:
            # 2. 验证用户名和密码
            user = authenticate(username=username, password=password)
            if user is None:
                try:
                    user_obj = User.objects.get(username=username)
                except User.DoesNotExist:
                    user_obj = None

                if user_obj and user_obj.password and "$" not in user_obj.password:
                    if user_obj.password == password:
                        user_obj.set_password(password)
                        user_obj.save(update_fields=["password"])
                        user = user_obj

                if user is None:
                    raise serializers.ValidationError({"detail": "用户名或密码错误。"})
        except OperationalError:
            raise serializers.ValidationError({"detail": "数据库连接失败，请确认 MySQL 服务已启动。"})

        self.user = user

        try:
            # 3. 验证用户是否属于该团队
            profile = ensure_user_profile(user)
            if profile.team != team:
                raise serializers.ValidationError({"detail": f"用户不属于团队 {team_code}。"})
        except OperationalError:
            raise serializers.ValidationError({"detail": "数据库连接失败，请确认 MySQL 服务已启动。"})

        # 4. 生成 Token 和 Session
        session_state, _ = UserSession.objects.select_for_update().get_or_create(user=user)
        session_state.session_version += 1
        session_state.save(update_fields=["session_version", "updated_at"])

        refresh = self.get_token(user)
        
        # 记录登录日志
        log_action(
            user=user,
            action='LOGIN',
            resource='系统',
            description=f'用户 {user.username} 登录团队 {team.code}',
            request=self.context.get('request')
        )
        
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = RefreshToken(attrs["refresh"])
        user_id = refresh.get("user_id")
        token_version = refresh.get("session_version")
        try:
            session_state = UserSession.objects.get(user_id=user_id)
        except UserSession.DoesNotExist as exc:
            raise serializers.ValidationError("登录状态不存在，请重新登录。") from exc

        if token_version != session_state.session_version:
            raise serializers.ValidationError("账号已在其他设备登录，请重新登录。")

        data = super().validate(attrs)
        access = refresh.access_token
        access["session_version"] = session_state.session_version
        data["access"] = str(access)
        return data


class RegisterSerializer(serializers.Serializer):
    team_name = serializers.CharField(max_length=64)
    team_code = serializers.CharField(max_length=32)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_team_code(self, value):
        if Team.objects.filter(code=value).exists():
            raise serializers.ValidationError("团队号已存在。")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在。")
        return value

    @transaction.atomic
    def create(self, validated_data):
        team = Team.objects.create(
            name=validated_data["team_name"],
            code=validated_data["team_code"]
        )
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"]
        )
        team.admin_user = user
        team.save(update_fields=["admin_user"])
        UserProfile.objects.create(user=user, team=team, role="ADMIN")
        UserSession.objects.get_or_create(user=user)
        return user


class SubAccountCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在。")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        request_user = request.user
        profile = ensure_user_profile(request_user)
        if profile.team.admin_user_id != request_user.id:
            raise serializers.ValidationError({"detail": "只有管理员可以创建账号。"})

        team = profile.team
        current_subaccounts = UserProfile.objects.filter(team=team, role="MEMBER").count()
        if current_subaccounts >= TEAM_MAX_SUB_ACCOUNTS:
            raise serializers.ValidationError(
                {"detail": f"团队 {team.code} 最多只能有 {TEAM_MAX_SUB_ACCOUNTS} 个成员账号。"}
            )

        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            is_staff=False,
            is_superuser=False,
        )
        UserProfile.objects.create(user=user, team=team, role="MEMBER")
        UserSession.objects.get_or_create(user=user)

        log_action(
            user=request_user,
            action="CREATE",
            resource="账号",
            description=f"创建成员账号：{user.username}",
            request=request,
        )

        return user
