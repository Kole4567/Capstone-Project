from django.urls import path
from .api_views import MonsterListView, MonsterDetailView

urlpatterns = [
    path(
        "api/v1/mhw/monsters/",
        MonsterListView.as_view(),
        name="mhw-monster-list",
    ),
    path(
        "api/v1/mhw/monsters/<int:id>/",
        MonsterDetailView.as_view(),
        name="mhw-monster-detail",
    ),
]