from django.db import models

from products.models import Product


class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory", verbose_name="商品")
    quantity = models.PositiveIntegerField(default=0, verbose_name="库存")
    warning_level = models.PositiveIntegerField(default=10, verbose_name="预警值")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "库存"
        verbose_name_plural = "库存"
        ordering = ["product__name"]

    @property
    def is_low_stock(self):
        return self.quantity <= self.warning_level

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
