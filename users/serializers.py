from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Team, UserProfile, UserSession

TEAM_MAX_SUB_ACCOUNTS = 3


def get_default_team():
    team, _ = Team.objects.get_or_create(code="TEAM001", defaults={"name": "默认团队"})
    return team


def ensure_user_profile(user):
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={"team": get_default_team()}
    )
    return profile


class UserSerializer(serializers.ModelSerializer):
    team_code = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "is_superuser", "is_staff", "team_code", "team_name"]

    def get_team_code(self, obj):
        return ensure_user_profile(obj).team.code

    def get_team_name(self, obj):
        return ensure_user_profile(obj).team.name


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

        # 1. 验证团队是否存在
        try:
            team = Team.objects.get(code=team_code)
        except Team.DoesNotExist:
            raise serializers.ValidationError({"detail": "团队号不存在。"})

        # 2. 验证用户名和密码
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError({"detail": "用户名或密码错误。"})

        self.user = user

        # 3. 验证用户是否属于该团队
        profile = ensure_user_profile(user)
        if profile.team != team:
            raise serializers.ValidationError({"detail": f"用户不属于团队 {team_code}。"})

        # 4. 生成 Token 和 Session
        session_state, _ = UserSession.objects.select_for_update().get_or_create(user=user)
        session_state.session_version += 1
        session_state.save(update_fields=["session_version", "updated_at"])

        refresh = self.get_token(user)
        
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


class SubAccountCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在。")
        return value

    def create(self, validated_data):
        request_user = self.context["request"].user
        profile = ensure_user_profile(request_user)
        team = profile.team

        current_subaccounts = (
            User.objects.filter(profile__team=team, is_superuser=False).count()
        )
        if current_subaccounts >= TEAM_MAX_SUB_ACCOUNTS:
            raise serializers.ValidationError(
                {"detail": f"团队 {team.code} 最多只能有 {TEAM_MAX_SUB_ACCOUNTS} 个子账号。"}
            )

        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            is_staff=False,
            is_superuser=False,
        )
        UserProfile.objects.create(user=user, team=team)
        UserSession.objects.get_or_create(user=user)
        return user
