from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import Inventory
from records.models import StockIn, StockOut


class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trend_map = {}
        today = timezone.localdate()
        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            trend_map[day.isoformat()] = {"day": day.isoformat(), "stockin": 0, "stockout": 0}

        stockin_records = list(StockIn.objects.only("created_at", "quantity"))
        stockout_records = list(StockOut.objects.only("created_at", "quantity"))

        stockin_totals = {}
        stockout_totals = {}

        for record in stockin_records:
            if not record.created_at:
                continue
            day = timezone.localtime(record.created_at).date().isoformat()
            stockin_totals[day] = stockin_totals.get(day, 0) + record.quantity
            if day in trend_map:
                trend_map[day]["stockin"] += record.quantity

        for record in stockout_records:
            if not record.created_at:
                continue
            day = timezone.localtime(record.created_at).date().isoformat()
            stockout_totals[day] = stockout_totals.get(day, 0) + record.quantity
            if day in trend_map:
                trend_map[day]["stockout"] += record.quantity

        stockin_trend_raw = [{"day": day, "total": total} for day, total in sorted(stockin_totals.items())]
        stockout_trend_raw = [{"day": day, "total": total} for day, total in sorted(stockout_totals.items())]
        trend_comparison = list(trend_map.values())

        category_share = list(
            Inventory.objects.select_related("product")
            .values("product__category")
            .annotate(total=Sum("quantity"))
            .order_by("-total")
        )
        top_products = list(
            StockOut.objects.values("product__name")
            .annotate(total=Sum("quantity"))
            .order_by("-total")[:5]
        )
        inventory_status = list(
            Inventory.objects.values("product__name", "quantity", "warning_level")
            .order_by("-quantity")[:6]
        )
        zero_inventory_products = list(
            Inventory.objects.select_related("product").filter(quantity__lte=0).values("product__name")
        )
        inventory_list = list(Inventory.objects.select_related("product").all())
        low_stock_items = [item for item in inventory_list if item.is_low_stock]

        return Response(
            {
                "stockin_trend": stockin_trend_raw,
                "stockout_trend": stockout_trend_raw,
                "trend_comparison": trend_comparison,
                "category_share": [
                    {"name": item["product__category"] or "未分类", "value": item["total"] or 0}
                    for item in category_share
                ],
                "top_products": [
                    {"name": item["product__name"], "value": item["total"] or 0}
                    for item in top_products
                ],
                "inventory_status": [
                    {
                        "name": item["product__name"],
                        "quantity": item["quantity"],
                        "warning_level": item["warning_level"],
                    }
                    for item in inventory_status
                ],
                "summary": {
                    "product_count": len(inventory_list),
                    "low_stock_count": len(low_stock_items),
                    "inventory_total": sum(item.quantity for item in inventory_list),
                    "stockin_total": sum((item["total"] or 0) for item in stockin_trend_raw),
                    "stockout_total": sum((item["total"] or 0) for item in stockout_trend_raw),
                    "low_stock_names": [item.product.name for item in low_stock_items[:5]],
                    "zero_inventory_count": len(zero_inventory_products),
                },
                "category_summary": {
                    "category_count": len(category_share),
                    "largest_category": (category_share[0]["product__category"] or "未分类") if category_share else "暂无数据",
                },
            }
        )
