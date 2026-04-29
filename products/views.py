from rest_framework import viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from inventory.models import Inventory
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Product.objects.all().select_related("inventory")

    def perform_create(self, serializer):
        product = serializer.save()
        Inventory.objects.get_or_create(product=product)
