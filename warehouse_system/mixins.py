from rest_framework.views import APIView
from rest_framework.response import Response


class TeamQuerySetMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        profile = getattr(user, "profile", None)
        if not profile:
            return queryset.none()
        team = profile.team
        if hasattr(queryset.model, "product"):
            return queryset.filter(product__team=team)
        if hasattr(queryset.model, "team"):
            return queryset.filter(team=team)
        return queryset


class TeamAnalyticsMixin:
    def get_team_filtered_queryset(self, model_class, related_field=None):
        user = self.request.user
        if not user.is_authenticated:
            return model_class.objects.none()
        profile = getattr(user, "profile", None)
        if not profile:
            return model_class.objects.none()
        team = profile.team
        if related_field:
            return model_class.objects.filter(**{related_field: team})
        return model_class.objects.filter(team=team)