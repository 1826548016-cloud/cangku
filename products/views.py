from rest_framework import viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from inventory.models import Inventory
from users.serializers import ensure_user_profile
from users.utils import log_action
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
        log_action(user, 'CREATE', '商品', f'创建商品: {product.name} ({product.sku})', self.request)

    def perform_update(self, serializer):
        product = serializer.save()
        log_action(self.request.user, 'UPDATE', '商品', f'修改商品: {product.name} ({product.sku})', self.request)

    def perform_destroy(self, instance):
        name, sku = instance.name, instance.sku
        instance.delete()
        log_action(self.request.user, 'DELETE', '商品', f'删除商品: {name} ({sku})', self.request)
