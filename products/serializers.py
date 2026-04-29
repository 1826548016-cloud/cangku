from rest_framework import serializers

from inventory.models import Inventory
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(source="inventory.quantity", read_only=True)
    warning_level = serializers.IntegerField(source="inventory.warning_level", read_only=True)
    is_low_stock = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    inventory_id = serializers.IntegerField(source="inventory.id", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "category",
            "price",
            "image",
            "image_url",
            "quantity",
            "warning_level",
            "is_low_stock",
            "inventory_id",
            "created_at",
            "updated_at",
        ]

    def get_is_low_stock(self, obj):
        inventory = getattr(obj, "inventory", None)
        return inventory.is_low_stock if inventory else False

    def get_image_url(self, obj):
        if not obj.image:
            return ""
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url

    def create(self, validated_data):
        product = super().create(validated_data)
        Inventory.objects.get_or_create(product=product)
        return product
