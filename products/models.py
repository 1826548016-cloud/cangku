from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=120, verbose_name="商品名称")
    sku = models.CharField(max_length=64, unique=True, verbose_name="SKU")
    category = models.CharField(max_length=80, blank=True, verbose_name="分类")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="单价")
    image = models.ImageField(upload_to="products/", blank=True, null=True, verbose_name="商品图片")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "商品"
        verbose_name_plural = "商品"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.sku})"
