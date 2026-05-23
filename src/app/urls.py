from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.auth_urls")),
    path("accounts/", include("allauth.urls")),
    path("recruiter/", include("apps.accounts.urls")),
    path("pwa/", include("pwa.urls")),
    path("", include("apps.common.urls")),
    path("api/", include("apps.security.api_urls")),
    path("api/", include("apps.accounts.api_urls")),
    path("api/", include("apps.candidates.api_urls")),
    path("api/", include("apps.credits.api_urls")),
    path("api/", include("apps.moderation.api_urls")),
    path("api/", include("apps.replication.api_urls")),
]


urlpatterns += [path("healthz/", lambda request: HttpResponse("ok", content_type="text/plain"))]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
