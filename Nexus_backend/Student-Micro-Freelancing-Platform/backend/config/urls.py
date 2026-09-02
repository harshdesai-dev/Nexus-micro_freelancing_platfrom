from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from authentication.views import me_view


def home(request):
    return JsonResponse({"success": True, "data": {}, "message": "NEXUS backend is running"})


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.urls")),
    path("api/users/me", me_view),
    path("api/", include("students.urls")),
    path("api/", include("clients.urls")),
    path("api/admin/", include("admin_panel.urls")),
    path("api/ai/", include("ai.urls")),
]
