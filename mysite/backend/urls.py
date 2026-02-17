from django.contrib import admin
from django.urls import include, path

# OpenAPI / Swagger
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Admin - Only need this ONCE
    path('admin/', admin.site.urls),

    # App Routes
    path('', include('MonsterHunterWorld.urls')), 
    path('weapons/', include('weapons.urls')),
    path('armors/', include('armors.urls')),
    path('charms/', include('charms.urls')),
    path('monsters/', include('monsters.urls')),

    # OpenAPI schema and API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]