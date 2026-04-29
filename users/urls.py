from django.urls import path

from .views import LoginView, ProfileView, RefreshView, TeamSubAccountView, RegisterView, AuditLogView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("me/", ProfileView.as_view(), name="me"),
    path("team/subaccounts/", TeamSubAccountView.as_view(), name="team-subaccounts"),
    path("audit-logs/", AuditLogView.as_view(), name="audit-logs"),
]
