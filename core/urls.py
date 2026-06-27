from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from core.views import custom_404

handler404 = 'core.views.custom_404'

urlpatterns = [

    path("admin/", admin.site.urls),

    path("", include("accounts.urls")),

    path("cases/", include("cases.urls")),

    path("404/", custom_404, name="page_404"),

    re_path(r'^.*$', custom_404),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)