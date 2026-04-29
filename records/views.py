import hashlib
from io import BytesIO

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfdoc
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import Inventory
from users.utils import log_action
from .models import StockIn, StockOut
from .serializers import StockInSerializer, StockOutSerializer


_original_md5 = hashlib.md5


def compatible_md5(*args, **kwargs):
    kwargs.pop("usedforsecurity", None)
    return _original_md5(*args, **kwargs)


hashlib.md5 = compatible_md5
pdfdoc.md5 = compatible_md5


def filter_records(queryset, search):
    queryset = queryset.select_related("product", "created_by", "product__inventory")
    if search:
        queryset = queryset.filter(
            Q(product__sku__icontains=search)
            | Q(product__name__icontains=search)
            | Q(note__icontains=search)
        )
    return queryset.order_by("-created_at")


def build_pdf_response(title, records):
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    styles["Title"].fontName = "STSong-Light"
    styles["Normal"].fontName = "STSong-Light"
    elements = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 12),
    ]

    table_data = [["时间", "商品", "SKU", "数量", "剩余库存", "备注", "操作人"]]
    for record in records:
        inventory = getattr(record.product, "inventory", None)
        table_data.append(
            [
                record.created_at.strftime("%Y-%m-%d %H:%M"),
                record.product.name,
                record.product.sku,
                str(record.quantity),
                str(inventory.quantity if inventory else 0),
                record.note or "-",
                record.created_by.username if record.created_by else "-",
            ]
        )

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{title}.pdf"'
    return response


class StockInViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = StockInSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return StockIn.objects.none()
        profile = getattr(user, "profile", None)
        if not profile:
            return StockIn.objects.none()
        team = profile.team
        return filter_records(
            StockIn.objects.filter(product__team=team).all(),
            self.request.query_params.get("search", "").strip()
        )

    def perform_create(self, serializer):
        user = self.request.user
        record = serializer.save(created_by=user)
        log_action(user, 'STOCK_IN', '入库', f'商品 {record.product.name} 入库 {record.quantity}', self.request)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        product_name = instance.product.name
        quantity = instance.quantity
        inventory, _ = Inventory.objects.get_or_create(product=instance.product)
        if inventory.quantity < instance.quantity:
            return Response({"detail": "当前库存不足，无法删除该入库记录。"}, status=400)
        inventory.quantity -= instance.quantity
        inventory.save(update_fields=["quantity", "updated_at"])
        instance.delete()
        log_action(request.user, 'DELETE', '入库记录', f'删除入库记录: {product_name} 数量 {quantity}', request)
        return Response(status=204)


class StockOutViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = StockOutSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return StockOut.objects.none()
        profile = getattr(user, "profile", None)
        if not profile:
            return StockOut.objects.none()
        team = profile.team
        return filter_records(
            StockOut.objects.filter(product__team=team).all(),
            self.request.query_params.get("search", "").strip()
        )

    def perform_create(self, serializer):
        user = self.request.user
        record = serializer.save(created_by=user)
        log_action(user, 'STOCK_OUT', '出库', f'商品 {record.product.name} 出库 {record.quantity}', self.request)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        product_name = instance.product.name
        quantity = instance.quantity
        inventory, _ = Inventory.objects.get_or_create(product=instance.product)
        inventory.quantity += instance.quantity
        inventory.save(update_fields=["quantity", "updated_at"])
        instance.delete()
        log_action(request.user, 'DELETE', '出库记录', f'删除出库记录: {product_name} 数量 {quantity}', request)
        return Response(status=204)


class StockInPDFExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "未认证"}, status=401)
        profile = getattr(user, "profile", None)
        if not profile:
            return Response({"detail": "用户无团队信息"}, status=400)
        team = profile.team
        records = filter_records(
            StockIn.objects.filter(product__team=team).all(),
            request.query_params.get("search", "").strip()
        )
        return build_pdf_response("入库记录报表", records)


class StockOutPDFExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "未认证"}, status=401)
        profile = getattr(user, "profile", None)
        if not profile:
            return Response({"detail": "用户无团队信息"}, status=400)
        team = profile.team
        records = filter_records(
            StockOut.objects.filter(product__team=team).all(),
            request.query_params.get("search", "").strip()
        )
        return build_pdf_response("出库记录报表", records)
