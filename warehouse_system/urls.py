from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/products/", include("products.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/records/", include("records.urls")),
    path("api/analytics/", include("analytics_app.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
