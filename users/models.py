from django.contrib.auth.models import User
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=64, unique=True, verbose_name="团队名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="团队号")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "团队"
        verbose_name_plural = "团队"

    def __str__(self):
        return f"{self.name}({self.code})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="members", verbose_name="所属团队")

    class Meta:
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料"

    def __str__(self):
        return f"{self.user.username} -> {self.team.code}"


class UserSession(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="session_state")
    session_version = models.PositiveIntegerField(default=0, verbose_name="登录版本")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "用户会话"
        verbose_name_plural = "用户会话"

    def __str__(self):
        return f"{self.user.username} - v{self.session_version}"
