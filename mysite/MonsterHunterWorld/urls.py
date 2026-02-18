from django.urls import path
from . import views

from .api_views import (
    # ==================================================
    # Monsters
    # ==================================================
    MonsterListView,
    MonsterListPagedView,
    MonsterDetailView,

    # ==================================================
    # Weapons
    # ==================================================
    WeaponListView,
    WeaponListPagedView,
    WeaponDetailView,

    # ==================================================
    # Skills
    # ==================================================
    SkillListView,
    SkillListPagedView,
    SkillDetailView,

    # ==================================================
    # Armors
    # ==================================================
    ArmorListView,
    ArmorListPagedView,
    ArmorDetailView,

    # ==================================================
    # Charms
    # ==================================================
    CharmListView,
    CharmListPagedView,
    CharmDetailView,

    # ==================================================
    # Decorations
    # ==================================================
    DecorationListView,
    DecorationListPagedView,
    DecorationDetailView,

    # ==================================================
    # Builds
    # ==================================================
    BuildListView,
    BuildListPagedView,
    BuildDetailView,

    # ==================================================
    # Build Stats (Placeholder)
    # ==================================================
    BuildStatsView,
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

    # ==================================================
    # Skills
    # ==================================================
    path(
        "api/v1/mhw/skills/",
        SkillListView.as_view(),
        name="mhw-skill-list",
    ),
    path(
        "api/v1/mhw/skills/paged/",
        SkillListPagedView.as_view(),
        name="mhw-skill-list-paged",
    ),
    path(
        "api/v1/mhw/skills/<int:id>/",
        SkillDetailView.as_view(),
        name="mhw-skill-detail",
    ),

    # ==================================================
    # Armors
    # ==================================================
    path(
        "api/v1/mhw/armors/",
        ArmorListView.as_view(),
        name="mhw-armor-list",
    ),
    path(
        "api/v1/mhw/armors/paged/",
        ArmorListPagedView.as_view(),
        name="mhw-armor-list-paged",
    ),
    path(
        "api/v1/mhw/armors/<int:id>/",
        ArmorDetailView.as_view(),
        name="mhw-armor-detail",
    ),

    # ==================================================
    # Charms
    # ==================================================
    path(
        "api/v1/mhw/charms/",
        CharmListView.as_view(),
        name="mhw-charm-list",
    ),
    path(
        "api/v1/mhw/charms/paged/",
        CharmListPagedView.as_view(),
        name="mhw-charm-list-paged",
    ),
    path(
        "api/v1/mhw/charms/<int:id>/",
        CharmDetailView.as_view(),
        name="mhw-charm-detail",
    ),

    # ==================================================
    # Decorations
    # ==================================================
    path(
        "api/v1/mhw/decorations/",
        DecorationListView.as_view(),
        name="mhw-decoration-list",
    ),
    path(
        "api/v1/mhw/decorations/paged/",
        DecorationListPagedView.as_view(),
        name="mhw-decoration-list-paged",
    ),
    path(
        "api/v1/mhw/decorations/<int:id>/",
        DecorationDetailView.as_view(),
        name="mhw-decoration-detail",
    ),

    # ==================================================
    # Builds
    # ==================================================
    path(
        "api/v1/mhw/builds/",
        BuildListView.as_view(),
        name="mhw-build-list",
    ),
    path(
        "api/v1/mhw/builds/paged/",
        BuildListPagedView.as_view(),
        name="mhw-build-list-paged",
    ),
    path(
        "api/v1/mhw/builds/<int:id>/",
        BuildDetailView.as_view(),
        name="mhw-build-detail",
    ),

    # ==================================================
    # Build Stats (Placeholder)
    # ==================================================
    path(
        "api/v1/mhw/builds/<int:id>/stats/",
        BuildStatsView.as_view(),
        name="mhw-build-stats",
    ),

    # This will now be the main page at 127.0.0.1:8000/
    path(
        "", views.home, name="home"
    ), 
]
