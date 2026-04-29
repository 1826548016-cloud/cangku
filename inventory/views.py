from rest_framework import mixins, viewsets

from .models import Inventory
from .serializers import InventorySerializer


class InventoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Inventory.objects.select_related("product").all()
    serializer_class = InventorySerializer
