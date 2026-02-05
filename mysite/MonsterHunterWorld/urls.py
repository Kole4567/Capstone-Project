from django.urls import path
from MonsterHunterWorld.api_views import (
    MonsterListView,
    MonsterDetailView,
)

urlpatterns = [
    path(
        "api/v1/mhw/monsters/",
        MonsterListView.as_view(),
        name="mhw-monster-list",
    ),
    path(
        "api/v1/mhw/monsters/<int:pk>/",
        MonsterDetailView.as_view(),
        name="mhw-monster-detail",
    ),
]