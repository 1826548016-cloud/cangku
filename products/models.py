from django.db import models

from users.models import Team


class Product(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="products", verbose_name="所属团队", null=True, blank=True)
    name = models.CharField(max_length=120, verbose_name="商品名称")
    sku = models.CharField(max_length=64, verbose_name="SKU")
    category = models.CharField(max_length=80, blank=True, verbose_name="分类")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="单价")
    image = models.ImageField(upload_to="products/", blank=True, null=True, verbose_name="商品图片")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "商品"
        verbose_name_plural = "商品"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["team", "sku"], name="unique_team_sku")
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"
