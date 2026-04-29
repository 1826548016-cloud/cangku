from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import StockInPDFExportView, StockInViewSet, StockOutPDFExportView, StockOutViewSet


router = DefaultRouter()
router.register("stockin", StockInViewSet, basename="stockin")
router.register("stockout", StockOutViewSet, basename="stockout")

urlpatterns = [
    path("stockin/export/pdf/", StockInPDFExportView.as_view(), name="stockin-export-pdf"),
    path("stockout/export/pdf/", StockOutPDFExportView.as_view(), name="stockout-export-pdf"),
]

urlpatterns += router.urls
