from rest_framework import viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from inventory.models import Inventory
from users.serializers import ensure_user_profile
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Product.objects.none()
        profile = ensure_user_profile(user)
        team = profile.team
        return Product.objects.filter(team=team).select_related("inventory")

    def perform_create(self, serializer):
        user = self.request.user
        profile = ensure_user_profile(user)
        product = serializer.save(team=profile.team)
        Inventory.objects.get_or_create(product=product)
