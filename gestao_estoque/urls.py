from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from inventory_management.admin import ProductAdmin


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventory_management.urls')),
    path('accounts/', include('accounts.urls')),
]

admin.site.get_urls = lambda: [
    path('admin/product/autocomplete/', ProductAdmin(admin.site).autocomplete_view, name='product_autocomplete'),
] + admin.site.get_urls()

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)