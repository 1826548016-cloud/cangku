from django.contrib.auth.models import User
from django.db import models

from products.models import Product


class BaseStockRecord(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="%(class)ss", verbose_name="商品")
    quantity = models.PositiveIntegerField(verbose_name="数量")
    note = models.CharField(max_length=255, blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="操作人",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class StockIn(BaseStockRecord):
    class Meta(BaseStockRecord.Meta):
        verbose_name = "入库记录"
        verbose_name_plural = "入库记录"


class StockOut(BaseStockRecord):
    class Meta(BaseStockRecord.Meta):
        verbose_name = "出库记录"
        verbose_name_plural = "出库记录"
