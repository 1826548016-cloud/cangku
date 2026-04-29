from rest_framework import mixins, viewsets

from users.serializers import ensure_user_profile
from .models import Inventory
from .serializers import InventorySerializer


class InventoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = InventorySerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Inventory.objects.none()
        profile = ensure_user_profile(user)
        team = profile.team
        return Inventory.objects.filter(product__team=team).select_related("product")
