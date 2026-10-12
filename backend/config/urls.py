from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from documents.views import DocumentViewSet, login, me

router = DefaultRouter()
router.register(r"documents", DocumentViewSet, basename="document")


def health(_request):
    """Lightweight health check for the deploy platform."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/login/", login, name="auth-login"),
    path("api/me/", me, name="me"),
    path("api/", include(router.urls)),
]
