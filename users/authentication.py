from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from .models import UserSession


class SingleSessionJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        token_version = validated_token.get("session_version")
        session_state, _ = UserSession.objects.get_or_create(user=user)

        if token_version is None or token_version != session_state.session_version:
            raise InvalidToken("账号已在其他设备登录，请重新登录。")

        return user
