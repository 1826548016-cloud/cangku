from rest_framework import serializers

from .models import Inventory


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Inventory
        fields = [
            "id",
            "product",
            "product_name",
            "sku",
            "quantity",
            "warning_level",
            "is_low_stock",
            "updated_at",
        ]
        read_only_fields = ["product", "quantity", "updated_at", "product_name", "sku", "is_low_stock"]
