from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination

from .models import Monster, Weapon, Skill, Armor
from .serializers import (
    MonsterListSerializer,
    MonsterDetailSerializer,
    WeaponListSerializer,
    WeaponDetailSerializer,
    SkillListSerializer,
    SkillDetailSerializer,
    ArmorListSerializer,
    ArmorDetailSerializer,
)


# ==================================================
# Monsters
# ==================================================
class MonsterListView(generics.ListAPIView):
    """
    GET /api/v1/mhw/monsters/

    Optional query parameters:
    - is_elder_dragon (boolean)
    - element (string, case-insensitive)
    - min_stars (integer, 1–3, requires element)
    - order_by (string)
    """

    serializer_class = MonsterListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
        "name",
        "monster_type",
        "is_elder_dragon",
    }

    def get_queryset(self):
        queryset = Monster.objects.all()
        params = self.request.query_params

        # --------------------------------------------------
        # Filter: is_elder_dragon
        # --------------------------------------------------
        is_elder = params.get("is_elder_dragon")
        if is_elder is not None:
            value = is_elder.strip().lower()
            if value in ("true", "1", "yes"):
                queryset = queryset.filter(is_elder_dragon=True)
            elif value in ("false", "0", "no"):
                queryset = queryset.filter(is_elder_dragon=False)

        # --------------------------------------------------
        # Filter: element + min_stars
        # --------------------------------------------------
        element = params.get("element")
        if element:
            element = element.strip()

            queryset = queryset.filter(
                weaknesses__kind="element",
                weaknesses__name__iexact=element,
            )

            min_stars = params.get("min_stars")
            if min_stars is not None:
                try:
                    min_stars_int = int(min_stars)
                    if 1 <= min_stars_int <= 3:
                        queryset = queryset.filter(
                            weaknesses__stars__gte=min_stars_int
                        )
                except ValueError:
                    pass

            # Required because weakness join can create duplicates
            queryset = queryset.distinct()

        # --------------------------------------------------
        # Ordering
        # --------------------------------------------------
        order_by = params.get("order_by")
        if order_by:
            field = order_by.lstrip("-")
            if field in self.ALLOWED_ORDER_FIELDS:
                queryset = queryset.order_by(order_by)
            else:
                # If invalid, fall back to a stable default order
                queryset = queryset.order_by("id")
        else:
            # Default order when no order_by is provided
            queryset = queryset.order_by("id")

        return queryset


class MonsterLimitOffsetPagination(LimitOffsetPagination):
    """
    Pagination settings for /monsters/paged/

    default_limit: items returned when limit is not specified
    max_limit: cap to prevent huge responses
    """
    default_limit = 50
    max_limit = 200


class MonsterListPagedView(MonsterListView):
    """
    GET /api/v1/mhw/monsters/paged/

    Same filters/order_by as /monsters/ but returns a paginated response:
    {
      "count": ...,
      "next": "...",
      "previous": "...",
      "results": [...]
    }
    """
    pagination_class = MonsterLimitOffsetPagination


class MonsterDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/mhw/monsters/{id}/
    """
    queryset = Monster.objects.all()
    serializer_class = MonsterDetailSerializer
    lookup_field = "id"


# ==================================================
# Weapons
# ==================================================
class WeaponListView(generics.ListAPIView):
    """
    GET /api/v1/mhw/weapons/

    Minimal MVP query parameters:
    - type (string) or weapon_type (string): exact match
    - element (string): case-insensitive match (e.g., Fire)
    - rarity (int): exact match
    - min_rarity (int)
    - max_rarity (int)
    - min_attack (int): compares against attack_raw
    - order_by (string): allowed fields only, supports "-" prefix
    """

    serializer_class = WeaponListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
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

        # --------------------------------------------------
        # Filter: weapon type (support both "type" and "weapon_type")
        # --------------------------------------------------
        weapon_type = params.get("type") or params.get("weapon_type")
        if weapon_type:
            queryset = queryset.filter(weapon_type=weapon_type.strip())

        # --------------------------------------------------
        # Filter: element (case-insensitive)
        # --------------------------------------------------
        element = params.get("element")
        if element:
            queryset = queryset.filter(element__iexact=element.strip())

        # --------------------------------------------------
        # Filter: rarity (exact match)
        # --------------------------------------------------
        rarity = params.get("rarity")
        if rarity is not None:
            try:
                queryset = queryset.filter(rarity=int(rarity))
            except ValueError:
                pass

        # --------------------------------------------------
        # Filter: rarity range (min/max)
        # --------------------------------------------------
        min_rarity = params.get("min_rarity")
        if min_rarity is not None:
            try:
                queryset = queryset.filter(rarity__gte=int(min_rarity))
            except ValueError:
                pass

        max_rarity = params.get("max_rarity")
        if max_rarity is not None:
            try:
                queryset = queryset.filter(rarity__lte=int(max_rarity))
            except ValueError:
                pass

        # --------------------------------------------------
        # Filter: min_attack (attack_raw >= N)
        # --------------------------------------------------
        min_attack = params.get("min_attack")
        if min_attack is not None:
            try:
                queryset = queryset.filter(attack_raw__gte=int(min_attack))
            except ValueError:
                pass

        # --------------------------------------------------
        # Ordering (validated whitelist)
        # --------------------------------------------------
        order_by = params.get("order_by")
        if order_by:
            field = order_by.lstrip("-")
            if field in self.ALLOWED_ORDER_FIELDS:
                queryset = queryset.order_by(order_by)
            else:
                queryset = queryset.order_by("id")
        else:
            queryset = queryset.order_by("id")

        return queryset


class WeaponLimitOffsetPagination(LimitOffsetPagination):
    """
    Pagination settings for /weapons/paged/

    default_limit: items returned when limit is not specified
    max_limit: cap to prevent huge responses
    """
    default_limit = 50
    max_limit = 200


class WeaponListPagedView(WeaponListView):
    """
    GET /api/v1/mhw/weapons/paged/

    Same filters/order_by as /weapons/ but returns a paginated response:
    {
      "count": ...,
      "next": "...",
      "previous": "...",
      "results": [...]
    }
    """
    pagination_class = WeaponLimitOffsetPagination


class WeaponDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/mhw/weapons/{id}/
    """
    queryset = Weapon.objects.all()
    serializer_class = WeaponDetailSerializer
    lookup_field = "id"


# ==================================================
# Skills
# ==================================================
class SkillListView(generics.ListAPIView):
    """
    GET /api/v1/mhw/skills/

    Minimal MVP query parameters:
    - name (string): case-insensitive contains (icontains)
    - min_level (int): max_level >= N
    - order_by (string): allowed fields only, supports "-" prefix
    """

    serializer_class = SkillListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
        "name",
        "max_level",
    }

    def get_queryset(self):
        queryset = Skill.objects.all()
        params = self.request.query_params

        # --------------------------------------------------
        # Filter: name contains (case-insensitive)
        # --------------------------------------------------
        name = params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name.strip())

        # --------------------------------------------------
        # Filter: min_level (max_level >= N)
        # --------------------------------------------------
        min_level = params.get("min_level")
        if min_level is not None:
            try:
                queryset = queryset.filter(max_level__gte=int(min_level))
            except ValueError:
                pass

        # --------------------------------------------------
        # Ordering (validated whitelist)
        # --------------------------------------------------
        order_by = params.get("order_by")
        if order_by:
            field = order_by.lstrip("-")
            if field in self.ALLOWED_ORDER_FIELDS:
                queryset = queryset.order_by(order_by)
            else:
                queryset = queryset.order_by("id")
        else:
            queryset = queryset.order_by("id")

        return queryset


class SkillLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class SkillListPagedView(SkillListView):
    """
    GET /api/v1/mhw/skills/paged/
    """
    pagination_class = SkillLimitOffsetPagination


class SkillDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/mhw/skills/{id}/
    """
    queryset = Skill.objects.all()
    serializer_class = SkillDetailSerializer
    lookup_field = "id"


# ==================================================
# Armor
# ==================================================
class ArmorListView(generics.ListAPIView):
    """
    GET /api/v1/mhw/armors/

    Minimal MVP query parameters:
    - type (string) or armor_type (string): case-insensitive exact match
      (common values from mhw-db: head, chest, gloves, waist, legs)
    - rarity (int): exact match
    - min_rarity (int)
    - max_rarity (int)
    - min_defense (int): compares against defense_base
    - has_skill (string): case-insensitive contains match on Skill.name (via ArmorSkill join)
    - order_by (string): allowed fields only, supports "-" prefix
    """

    serializer_class = ArmorListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
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

        # --------------------------------------------------
        # Filter: armor type (support both "type" and "armor_type")
        # --------------------------------------------------
        armor_type = params.get("type") or params.get("armor_type")
        if armor_type:
            queryset = queryset.filter(armor_type__iexact=armor_type.strip())

        # --------------------------------------------------
        # Filter: rarity (exact match)
        # --------------------------------------------------
        rarity = params.get("rarity")
        if rarity is not None:
            try:
                queryset = queryset.filter(rarity=int(rarity))
            except ValueError:
                pass

        # --------------------------------------------------
        # Filter: rarity range (min/max)
        # --------------------------------------------------
        min_rarity = params.get("min_rarity")
        if min_rarity is not None:
            try:
                queryset = queryset.filter(rarity__gte=int(min_rarity))
            except ValueError:
                pass

        max_rarity = params.get("max_rarity")
        if max_rarity is not None:
            try:
                queryset = queryset.filter(rarity__lte=int(max_rarity))
            except ValueError:
                pass

        # --------------------------------------------------
        # Filter: min_defense (defense_base >= N)
        # --------------------------------------------------
        min_defense = params.get("min_defense")
        if min_defense is not None:
            try:
                queryset = queryset.filter(defense_base__gte=int(min_defense))
            except ValueError:
                pass

        # --------------------------------------------------
        # Filter: has_skill (case-insensitive contains on Skill.name)
        # - Uses ArmorSkill join: armor_skills__skill__name__icontains
        # - Requires distinct() to avoid duplicates
        # --------------------------------------------------
        has_skill = params.get("has_skill")
        if has_skill:
            queryset = queryset.filter(
                armor_skills__skill__name__icontains=has_skill.strip()
            ).distinct()

        # --------------------------------------------------
        # Ordering (validated whitelist)
        # --------------------------------------------------
        order_by = params.get("order_by")
        if order_by:
            field = order_by.lstrip("-")
            if field in self.ALLOWED_ORDER_FIELDS:
                queryset = queryset.order_by(order_by)
            else:
                queryset = queryset.order_by("id")
        else:
            queryset = queryset.order_by("id")

        return queryset


class ArmorLimitOffsetPagination(LimitOffsetPagination):
    """
    Pagination settings for /armors/paged/

    default_limit: items returned when limit is not specified
    max_limit: cap to prevent huge responses
    """
    default_limit = 50
    max_limit = 200


class ArmorListPagedView(ArmorListView):
    """
    GET /api/v1/mhw/armors/paged/
    """
    pagination_class = ArmorLimitOffsetPagination


class ArmorDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/mhw/armors/{id}/
    """
    queryset = Armor.objects.all()
    serializer_class = ArmorDetailSerializer
    lookup_field = "id"