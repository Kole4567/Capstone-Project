from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from .models import Monster, Weapon, Skill, Armor, Build, Charm, Decoration
from .serializers import (
    MonsterListSerializer,
    MonsterDetailSerializer,
    WeaponListSerializer,
    WeaponDetailSerializer,
    SkillListSerializer,
    SkillDetailSerializer,
    ArmorListSerializer,
    ArmorDetailSerializer,
    BuildListSerializer,
    BuildDetailSerializer,
    BuildStatsSerializer,
    CharmListSerializer,
    CharmDetailSerializer,
    DecorationListSerializer,
    DecorationDetailSerializer,
)


# ==================================================
# Monsters
# ==================================================
class MonsterListView(generics.ListAPIView):
    serializer_class = MonsterListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
        "external_id",
        "name",
        "monster_type",
        "is_elder_dragon",
    }

    def get_queryset(self):
        queryset = Monster.objects.all()
        params = self.request.query_params

        is_elder = params.get("is_elder_dragon")
        if is_elder is not None:
            value = is_elder.strip().lower()
            if value in ("true", "1", "yes"):
                queryset = queryset.filter(is_elder_dragon=True)
            elif value in ("false", "0", "no"):
                queryset = queryset.filter(is_elder_dragon=False)

        element = params.get("element")
        if element:
            queryset = queryset.filter(
                weaknesses__kind="element",
                weaknesses__name__iexact=element.strip(),
            )

            min_stars = params.get("min_stars")
            if min_stars is not None:
                try:
                    min_stars = int(min_stars)
                    if 1 <= min_stars <= 3:
                        queryset = queryset.filter(weaknesses__stars__gte=min_stars)
                except ValueError:
                    pass

            queryset = queryset.distinct()

        order_by = params.get("order_by")
        if order_by and order_by.lstrip("-") in self.ALLOWED_ORDER_FIELDS:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by("id")

        return queryset


class MonsterLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class MonsterListPagedView(MonsterListView):
    pagination_class = MonsterLimitOffsetPagination


class MonsterDetailView(generics.RetrieveAPIView):
    # Prefetch weaknesses to avoid N+1 when serializer nests weaknesses
    queryset = Monster.objects.all().prefetch_related("weaknesses")
    serializer_class = MonsterDetailSerializer
    lookup_field = "external_id"


# ==================================================
# Weapons
# ==================================================
class WeaponListView(generics.ListAPIView):
    serializer_class = WeaponListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
        "external_id",
        "name",
        "weapon_type",
        "rarity",
        "attack_raw",
        "affinity",
        "element",
    }

    def get_queryset(self):
        queryset = Weapon.objects.all()
        params = self.request.query_params

        weapon_type = params.get("type") or params.get("weapon_type")
        if weapon_type:
            queryset = queryset.filter(weapon_type=weapon_type.strip())

        element = params.get("element")
        if element:
            queryset = queryset.filter(element__iexact=element.strip())

        for key, lookup in [
            ("rarity", "rarity"),
            ("min_rarity", "rarity__gte"),
            ("max_rarity", "rarity__lte"),
            ("min_attack", "attack_raw__gte"),
        ]:
            val = params.get(key)
            if val is not None:
                try:
                    queryset = queryset.filter(**{lookup: int(val)})
                except ValueError:
                    pass

        order_by = params.get("order_by")
        if order_by and order_by.lstrip("-") in self.ALLOWED_ORDER_FIELDS:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by("id")

        return queryset


class WeaponLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class WeaponListPagedView(WeaponListView):
    pagination_class = WeaponLimitOffsetPagination


class WeaponDetailView(generics.RetrieveAPIView):
    queryset = Weapon.objects.all()
    serializer_class = WeaponDetailSerializer
    lookup_field = "external_id"


# ==================================================
# Skills
# ==================================================
class SkillListView(generics.ListAPIView):
    serializer_class = SkillListSerializer
    ALLOWED_ORDER_FIELDS = {"id", "external_id", "name", "max_level"}

    def get_queryset(self):
        queryset = Skill.objects.all()
        params = self.request.query_params

        if name := params.get("name"):
            queryset = queryset.filter(name__icontains=name.strip())

        if min_level := params.get("min_level"):
            try:
                queryset = queryset.filter(max_level__gte=int(min_level))
            except ValueError:
                pass

        order_by = params.get("order_by")
        if order_by and order_by.lstrip("-") in self.ALLOWED_ORDER_FIELDS:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by("id")

        return queryset


class SkillLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class SkillListPagedView(SkillListView):
    pagination_class = SkillLimitOffsetPagination


class SkillDetailView(generics.RetrieveAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillDetailSerializer
    lookup_field = "external_id"


# ==================================================
# Armor
# ==================================================
class ArmorListView(generics.ListAPIView):
    serializer_class = ArmorListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
        "external_id",
        "name",
        "armor_type",
        "rarity",
        "defense_base",
        "defense_max",
        "defense_augmented",
        "slot_1",
        "slot_2",
        "slot_3",
    }

    def get_queryset(self):
        queryset = Armor.objects.all()
        params = self.request.query_params

        if armor_type := (params.get("type") or params.get("armor_type")):
            queryset = queryset.filter(armor_type__iexact=armor_type.strip())

        for key, lookup in [
            ("rarity", "rarity"),
            ("min_rarity", "rarity__gte"),
            ("max_rarity", "rarity__lte"),
            ("min_defense", "defense_base__gte"),
        ]:
            val = params.get(key)
            if val is not None:
                try:
                    queryset = queryset.filter(**{lookup: int(val)})
                except ValueError:
                    pass

        if has_skill := params.get("has_skill"):
            queryset = queryset.filter(
                armor_skills__skill__name__icontains=has_skill.strip()
            ).distinct()

        order_by = params.get("order_by")
        if order_by and order_by.lstrip("-") in self.ALLOWED_ORDER_FIELDS:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by("id")

        return queryset


class ArmorLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class ArmorListPagedView(ArmorListView):
    pagination_class = ArmorLimitOffsetPagination


class ArmorDetailView(generics.RetrieveAPIView):
    # Prefetch armor_skills->skill to avoid N+1 in nested serializer
    queryset = Armor.objects.all().prefetch_related("armor_skills__skill")
    serializer_class = ArmorDetailSerializer
    lookup_field = "external_id"


# ==================================================
# Charms
# ==================================================
class CharmListView(generics.ListAPIView):
    serializer_class = CharmListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
        "external_id",
        "name",
        "rarity",
    }

    def get_queryset(self):
        queryset = Charm.objects.all()
        params = self.request.query_params

        if name := params.get("name"):
            queryset = queryset.filter(name__icontains=name.strip())

        for key, lookup in [
            ("rarity", "rarity"),
            ("min_rarity", "rarity__gte"),
            ("max_rarity", "rarity__lte"),
        ]:
            val = params.get(key)
            if val is not None:
                try:
                    queryset = queryset.filter(**{lookup: int(val)})
                except ValueError:
                    pass

        order_by = params.get("order_by")
        if order_by and order_by.lstrip("-") in self.ALLOWED_ORDER_FIELDS:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by("id")

        return queryset


class CharmLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class CharmListPagedView(CharmListView):
    pagination_class = CharmLimitOffsetPagination


class CharmDetailView(generics.RetrieveAPIView):
    # Prefetch charm_skills->skill to avoid N+1
    queryset = Charm.objects.all().prefetch_related("charm_skills__skill")
    serializer_class = CharmDetailSerializer
    lookup_field = "external_id"


# ==================================================
# Decorations
# ==================================================
class DecorationListView(generics.ListAPIView):
    serializer_class = DecorationListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
        "external_id",
        "name",
        "rarity",
    }

    def get_queryset(self):
        queryset = Decoration.objects.all()
        params = self.request.query_params

        if name := params.get("name"):
            queryset = queryset.filter(name__icontains=name.strip())

        for key, lookup in [
            ("rarity", "rarity"),
            ("min_rarity", "rarity__gte"),
            ("max_rarity", "rarity__lte"),
        ]:
            val = params.get(key)
            if val is not None:
                try:
                    queryset = queryset.filter(**{lookup: int(val)})
                except ValueError:
                    pass

        # Optional convenience filter: decorations that grant a skill by name
        if has_skill := params.get("has_skill"):
            queryset = queryset.filter(
                decoration_skills__skill__name__icontains=has_skill.strip()
            ).distinct()

        order_by = params.get("order_by")
        if order_by and order_by.lstrip("-") in self.ALLOWED_ORDER_FIELDS:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by("id")

        return queryset


class DecorationLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class DecorationListPagedView(DecorationListView):
    pagination_class = DecorationLimitOffsetPagination


class DecorationDetailView(generics.RetrieveAPIView):
    # Prefetch decoration_skills->skill to avoid N+1
    queryset = Decoration.objects.all().prefetch_related("decoration_skills__skill")
    serializer_class = DecorationDetailSerializer
    lookup_field = "external_id"


# ==================================================
# Builds
# ==================================================
class BuildListView(generics.ListCreateAPIView):
    ALLOWED_ORDER_FIELDS = {"id", "name", "created_at", "updated_at"}

    def get_queryset(self):
        # select_related for direct FK, prefetch for nested build parts
        queryset = (
            Build.objects.all()
            .select_related("weapon", "charm")
            .prefetch_related(
                "armor_pieces__armor",
                "decorations__decoration",
            )
        )
        params = self.request.query_params

        if name := params.get("name"):
            queryset = queryset.filter(name__icontains=name.strip())

        if weapon_type := params.get("weapon_type"):
            queryset = queryset.filter(weapon__weapon_type=weapon_type.strip())

        # Optional convenience filter: builds that use a specific charm
        if charm_name := params.get("charm_name"):
            queryset = queryset.filter(charm__name__icontains=charm_name.strip())

        order_by = params.get("order_by")
        if order_by and order_by.lstrip("-") in self.ALLOWED_ORDER_FIELDS:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by("id")

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            from .serializers import BuildCreateUpdateSerializer

            return BuildCreateUpdateSerializer
        return BuildListSerializer


class BuildLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class BuildListPagedView(generics.ListAPIView):
    serializer_class = BuildListSerializer
    pagination_class = BuildLimitOffsetPagination

    queryset = (
        Build.objects.all()
        .select_related("weapon", "charm")
        .prefetch_related(
            "armor_pieces__armor",
            "decorations__decoration",
        )
        .order_by("id")
    )


class BuildDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = (
        Build.objects.all()
        .select_related("weapon", "charm")
        .prefetch_related(
            "armor_pieces__armor",
            "decorations__decoration",
        )
    )
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            from .serializers import BuildCreateUpdateSerializer

            return BuildCreateUpdateSerializer
        return BuildDetailSerializer


# ==================================================
# Build Stats (Placeholder – MHW STYLE CONTRACT)
# ==================================================
class BuildStatsView(generics.RetrieveAPIView):
    """
    GET /api/v1/mhw/builds/{id}/stats/

    Placeholder endpoint for calculated build results.
    (No real calculations yet, but response matches the final contract)
    """

    queryset = Build.objects.all()
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        build = self.get_object()

        # IMPORTANT:
        # This MUST match BuildStatsSerializer contract in serializers.py
        data = {
            "build_id": build.id,
            "stats": {
                "attack": {"raw": 0, "display": 0},
                "affinity": 0,
                "element": {"type": None, "value": 0},
                "defense": 0,
                "resistances": {
                    "fire": 0,
                    "water": 0,
                    "thunder": 0,
                    "ice": 0,
                    "dragon": 0,
                },
            },
            "skills": [],
            "set_bonuses": [],
        }

        serializer = BuildStatsSerializer(instance=data)
        return Response(serializer.data)