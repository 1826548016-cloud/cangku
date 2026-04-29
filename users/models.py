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


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', '创建'),
        ('UPDATE', '修改'),
        ('DELETE', '删除'),
        ('LOGIN', '登录'),
        ('STOCK_IN', '入库'),
        ('STOCK_OUT', '出库'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="audit_logs", verbose_name="所属团队")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="操作人")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="动作")
    resource = models.CharField(max_length=100, verbose_name="操作对象")
    description = models.TextField(verbose_name="详细描述")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"

