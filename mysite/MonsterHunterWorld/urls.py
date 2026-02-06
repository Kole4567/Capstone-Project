from django.urls import path

from .api_views import (
    # Monsters
    MonsterListView,
    MonsterListPagedView,
    MonsterDetailView,
    # Weapons
    WeaponListView,
    WeaponListPagedView,
    WeaponDetailView,
)

urlpatterns = [
    # ==================================================
    # Monsters
    # ==================================================
    path(
        "api/v1/mhw/monsters/",
        MonsterListView.as_view(),
        name="mhw-monster-list",
    ),
    path(
        "api/v1/mhw/monsters/paged/",
        MonsterListPagedView.as_view(),
        name="mhw-monster-list-paged",
    ),
    path(
        "api/v1/mhw/monsters/<int:id>/",
        MonsterDetailView.as_view(),
        name="mhw-monster-detail",
    ),

    # ==================================================
    # Weapons
    # ==================================================
    path(
        "api/v1/mhw/weapons/",
        WeaponListView.as_view(),
        name="mhw-weapon-list",
    ),
    path(
        "api/v1/mhw/weapons/paged/",
        WeaponListPagedView.as_view(),
        name="mhw-weapon-list-paged",
    ),
    path(
        "api/v1/mhw/weapons/<int:id>/",
        WeaponDetailView.as_view(),
        name="mhw-weapon-detail",
    ),
]