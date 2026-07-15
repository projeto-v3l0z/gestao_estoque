from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.views.static import serve


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventory_management.urls')),
    path('accounts/', include('accounts.urls')),
    path('select2/', include('django_select2.urls')),
]

# Static files are served by WhiteNoise (see MIDDLEWARE). Media uploads have
# no equivalent, so Django serves them directly here regardless of DEBUG —
# fine for this app's low traffic; move to object storage if that changes.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]