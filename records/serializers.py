from django.db import transaction
from rest_framework import serializers

from inventory.models import Inventory
from .models import StockIn, StockOut


class BaseRecordSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    operator = serializers.CharField(source="created_by.username", read_only=True)
    remaining_inventory = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "id",
            "product",
            "product_name",
            "sku",
            "quantity",
            "note",
            "created_at",
            "created_by",
            "operator",
            "remaining_inventory",
        ]
        read_only_fields = ["created_at", "created_by", "product_name", "sku", "operator", "remaining_inventory"]

    def get_remaining_inventory(self, obj):
        inventory = getattr(obj.product, "inventory", None)
        return inventory.quantity if inventory else 0


class StockInSerializer(BaseRecordSerializer):
    class Meta(BaseRecordSerializer.Meta):
        model = StockIn

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        record = StockIn.objects.create(**validated_data)
        inventory, _ = Inventory.objects.get_or_create(product=record.product)
        inventory.quantity += record.quantity
        inventory.save(update_fields=["quantity", "updated_at"])
        return record


class StockOutSerializer(BaseRecordSerializer):
    class Meta(BaseRecordSerializer.Meta):
        model = StockOut

    def validate(self, attrs):
        product = attrs["product"]
        quantity = attrs["quantity"]
        inventory, _ = Inventory.objects.get_or_create(product=product)
        if inventory.quantity < quantity:
            raise serializers.ValidationError("库存不足，无法出库。")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        record = StockOut.objects.create(**validated_data)
        inventory, _ = Inventory.objects.get_or_create(product=record.product)
        if inventory.quantity < record.quantity:
            raise serializers.ValidationError("库存不足，无法出库。")
        inventory.quantity -= record.quantity
        inventory.save(update_fields=["quantity", "updated_at"])
        return record
