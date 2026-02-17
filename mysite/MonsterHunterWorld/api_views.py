from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from rest_framework import generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from .models import (
    Armor,
    ArmorSkill,
    Build,
    Charm,
    CharmSkill,
    Decoration,
    DecorationSkill,
    Monster,
    SetBonus,
    SetBonusRank,
    Skill,
    Weapon,
)
from .serializers import (
    ArmorDetailSerializer,
    ArmorListSerializer,
    BuildDetailSerializer,
    BuildListSerializer,
    BuildStatsSerializer,
    CharmDetailSerializer,
    CharmListSerializer,
    DecorationDetailSerializer,
    DecorationListSerializer,
    MonsterDetailSerializer,
    MonsterListSerializer,
    SkillDetailSerializer,
    SkillListSerializer,
    WeaponDetailSerializer,
    WeaponListSerializer,
)

# ==================================================
# Monsters
# ==================================================
class MonsterListView(generics.ListAPIView):
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
    queryset = Monster.objects.all()
    serializer_class = MonsterDetailSerializer
    lookup_field = "id"


# ==================================================
# Weapons
# ==================================================
class WeaponListView(generics.ListAPIView):
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
    lookup_field = "id"


# ==================================================
# Skills
# ==================================================
class SkillListView(generics.ListAPIView):
    serializer_class = SkillListSerializer
    ALLOWED_ORDER_FIELDS = {"id", "name", "max_level"}

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
    lookup_field = "id"


# ==================================================
# Armor
# ==================================================
class ArmorListView(generics.ListAPIView):
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
    queryset = Armor.objects.all()
    serializer_class = ArmorDetailSerializer
    lookup_field = "id"


# ==================================================
# Charms
# ==================================================
class CharmListView(generics.ListAPIView):
    serializer_class = CharmListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
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
    queryset = Charm.objects.all()
    serializer_class = CharmDetailSerializer
    lookup_field = "id"


# ==================================================
# Decorations
# ==================================================
class DecorationListView(generics.ListAPIView):
    serializer_class = DecorationListSerializer

    ALLOWED_ORDER_FIELDS = {
        "id",
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
    queryset = Decoration.objects.all()
    serializer_class = DecorationDetailSerializer
    lookup_field = "id"


# ==================================================
# Builds
# ==================================================
class BuildListView(generics.ListCreateAPIView):
    ALLOWED_ORDER_FIELDS = {"id", "name", "created_at", "updated_at"}

    def get_queryset(self):
        queryset = Build.objects.all()
        params = self.request.query_params

        if name := params.get("name"):
            queryset = queryset.filter(name__icontains=name.strip())

        if weapon_type := params.get("weapon_type"):
            queryset = queryset.filter(weapon__weapon_type=weapon_type.strip())

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
    queryset = Build.objects.all()


class BuildDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Build.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            from .serializers import BuildCreateUpdateSerializer

            return BuildCreateUpdateSerializer
        return BuildDetailSerializer


# ==================================================
# Build Stats (MHW STYLE CONTRACT)
# ==================================================
@dataclass(frozen=True)
class _SetKey:
    """
    A stable key for grouping armor pieces into the same set for set-bonus evaluation.

    We prefer armor_set_bonus_external_id because it directly maps to the set bonus entity.
    When absent, we fall back to armor_set_external_id, and finally armor_set_name.
    """

    bonus_id: Optional[int]
    set_id: Optional[int]
    set_name: str


class BuildStatsView(generics.RetrieveAPIView):
    """
    GET /api/v1/mhw/builds/{id}/stats/

    MHW-like behavior implemented here:
    - Weapon stats:
      - attack_raw / attack_display / affinity / element from Build.weapon
      - element block is present even if empty (serializer contract)
    - Set bonus progress:
      - Counts equipped armor pieces per set bonus group.
      - Evaluates activation based on SetBonusRank "pieces" thresholds.
      - Returns one row per threshold (2p/3p/4p etc.) with active flags.
    - Skills (MHW-like aggregation):
      - Aggregates skills from: armor + charm + decorations + set_bonus
      - Dedup by skill_id (IMPORTANT: skill_id here means Skill.external_id)
      - Sum levels per source, then cap to Skill.max_level
      - sources dict tracks contribution: {"armor": x, "charm": x, "decoration": x, "set_bonus": x}
    - Defense + Resistances:
      - Defense sums armor.defense_base
      - Resistances sum armor resistance fields (res_fire/res_water/res_thunder/res_ice/res_dragon)
    - Output is always passed through BuildStatsSerializer to keep the API contract stable.
    """

    serializer_class = BuildStatsSerializer
    queryset = Build.objects.all()
    lookup_field = "id"

    # ------------------------------
    # Set grouping helpers
    # ------------------------------
    def _make_set_key(self, armor: Armor) -> Optional[_SetKey]:
        """Build a grouping key for set-bonus counting."""
        bonus_id = getattr(armor, "armor_set_bonus_external_id", None)
        set_id = getattr(armor, "armor_set_external_id", None)
        set_name = (getattr(armor, "armor_set_name", "") or "").strip()

        if bonus_id is None and set_id is None and not set_name:
            return None

        return _SetKey(
            bonus_id=int(bonus_id) if bonus_id is not None else None,
            set_id=int(set_id) if set_id is not None else None,
            set_name=set_name or "Unknown Set",
        )

    def _get_equipped_armors(self, build: Build) -> List[Armor]:
        """Return Armor objects that are actually equipped on this build."""
        out: List[Armor] = []
        for p in build.armor_pieces.select_related("armor").all():
            if p.armor_id:
                out.append(p.armor)
        return out

    def _count_equipped_set_pieces(
        self, build: Build
    ) -> Tuple[Dict[_SetKey, int], Dict[_SetKey, Dict[str, object]]]:
        """
        Count equipped armor pieces per set key.

        Returns:
          counts: {set_key: piece_count}
          meta:   {set_key: {"name": str, "bonus_id": Optional[int], "set_id": Optional[int], "rank": Optional[str]}}
        """
        armor_pieces = build.armor_pieces.select_related("armor").all()

        counts: Dict[_SetKey, int] = defaultdict(int)
        meta: Dict[_SetKey, Dict[str, object]] = {}

        for p in armor_pieces:
            if not p.armor_id:
                continue

            a = p.armor
            key = self._make_set_key(a)
            if key is None:
                continue

            counts[key] += 1

            if key not in meta:
                meta[key] = {
                    "name": key.set_name,
                    "bonus_id": key.bonus_id,
                    "set_id": key.set_id,
                    "rank": getattr(a, "armor_set_rank", None),
                }

        return counts, meta

    # ------------------------------
    # Small helper for tolerant int conversion
    # ------------------------------
    def _pick_int_field(self, obj: object, candidates: List[str], default: int = 0) -> int:
        """
        Try multiple attribute names and return the first valid int-like value.
        """
        for name in candidates:
            if hasattr(obj, name):
                val = getattr(obj, name)
                if val is None:
                    return default
                try:
                    return int(val)
                except (TypeError, ValueError):
                    return default
        return default

    # ------------------------------
    # Weapon stats (integration)
    # ------------------------------
    def _compute_weapon_stats(self, build: Build) -> Tuple[Dict[str, int], int, Dict[str, object]]:
        """
        Integrate weapon into the stats block.

        Contract mapping:
          - stats.attack.raw     -> Weapon.attack_raw
          - stats.attack.display -> Weapon.attack_display (fallback to raw if missing)
          - stats.affinity       -> Weapon.affinity
          - stats.element        -> {type: Weapon.element, value: Weapon.element_damage} (or {type: None, value: 0})
        """
        if not build.weapon_id:
            attack = {"raw": 0, "display": 0}
            affinity = 0
            element = {"type": None, "value": 0}
            return attack, affinity, element

        # Fetch from FK object if present; otherwise query by id (defensive)
        w: Optional[Weapon] = getattr(build, "weapon", None)
        if w is None:
            w = Weapon.objects.filter(id=build.weapon_id).first()

        if not w:
            return {"raw": 0, "display": 0}, 0, {"type": None, "value": 0}

        raw = self._pick_int_field(w, ["attack_raw"], default=0)
        display = self._pick_int_field(w, ["attack_display"], default=raw)
        affinity = self._pick_int_field(w, ["affinity"], default=0)

        element_type = (getattr(w, "element", None) or None)
        element_value = self._pick_int_field(w, ["element_damage"], default=0)

        if not element_type:
            element = {"type": None, "value": 0}
        else:
            element = {"type": str(element_type), "value": int(element_value)}

        attack = {"raw": int(raw), "display": int(display)}
        return attack, int(affinity), element

    # ------------------------------
    # Defense + Resistances
    # ------------------------------
    def _compute_defense(self, build: Build) -> int:
        total = 0
        for a in self._get_equipped_armors(build):
            total += self._pick_int_field(a, ["defense_base"], default=0)
        return int(total)

    def _compute_resistances(self, build: Build) -> Dict[str, int]:
        out = {"fire": 0, "water": 0, "thunder": 0, "ice": 0, "dragon": 0}

        for a in self._get_equipped_armors(build):
            out["fire"] += self._pick_int_field(a, ["res_fire"], default=0)
            out["water"] += self._pick_int_field(a, ["res_water"], default=0)
            out["thunder"] += self._pick_int_field(a, ["res_thunder"], default=0)
            out["ice"] += self._pick_int_field(a, ["res_ice"], default=0)
            out["dragon"] += self._pick_int_field(a, ["res_dragon"], default=0)

        return {k: int(v) for k, v in out.items()}

    # ------------------------------
    # Set bonus rows (thresholds)
    # ------------------------------
    def _compute_set_bonuses(self, build: Build) -> List[Dict[str, object]]:
        counts, meta = self._count_equipped_set_pieces(build)

        bonus_ids = sorted({k.bonus_id for k in counts.keys() if k.bonus_id is not None})
        ranks_by_bonus: Dict[int, List[SetBonusRank]] = defaultdict(list)

        if bonus_ids:
            qs = (
                SetBonusRank.objects.select_related("set_bonus", "skill")
                .filter(set_bonus__external_id__in=bonus_ids)
                .order_by("set_bonus__external_id", "pieces", "skill__name", "level")
            )
            for r in qs:
                ranks_by_bonus[int(r.set_bonus.external_id)].append(r)

        out: List[Dict[str, object]] = []

        for key, equipped_pieces in sorted(
            counts.items(), key=lambda x: (-x[1], x[0].set_name.lower())
        ):
            info = meta.get(key) or {}
            bonus_id = key.bonus_id

            if bonus_id is None:
                out.append(
                    {
                        "name": info.get("name") or "Unknown Set",
                        "pieces": int(equipped_pieces),
                        "active": False,
                    }
                )
                continue

            ranks = ranks_by_bonus.get(int(bonus_id), [])
            if not ranks:
                out.append(
                    {
                        "name": info.get("name") or "Unknown Set",
                        "pieces": int(equipped_pieces),
                        "active": False,
                    }
                )
                continue

            set_bonus_name = ranks[0].set_bonus.name
            thresholds = sorted({int(r.pieces) for r in ranks if int(r.pieces) > 0})

            if not thresholds:
                out.append({"name": set_bonus_name, "pieces": int(equipped_pieces), "active": False})
                continue

            for t in thresholds:
                out.append(
                    {
                        "name": set_bonus_name,
                        "pieces": int(t),
                        "active": bool(int(equipped_pieces) >= int(t)),
                    }
                )

        out.sort(
            key=lambda x: (
                str(x.get("name") or "").lower(),
                int(x.get("pieces") or 0),
            )
        )
        return out

    # ------------------------------
    # Set bonus unlocked skills (raw contributions)
    # ------------------------------
    def _compute_set_bonus_skill_contribs(self, build: Build) -> Dict[int, int]:
        """
        Return {skill_external_id: level_from_set_bonus} for ACTIVE thresholds.
        If the same skill appears multiple times, keep the highest level.
        """
        counts, _meta = self._count_equipped_set_pieces(build)

        bonus_counts: Dict[int, int] = defaultdict(int)
        for key, n in counts.items():
            if key.bonus_id is None:
                continue
            bonus_counts[int(key.bonus_id)] += int(n)

        if not bonus_counts:
            return {}

        bonus_ids = sorted(bonus_counts.keys())

        ranks = (
            SetBonusRank.objects.select_related("set_bonus", "skill")
            .filter(set_bonus__external_id__in=bonus_ids)
            .order_by("set_bonus__external_id", "pieces", "skill__name", "level")
        )

        best: Dict[int, int] = {}
        for r in ranks:
            bonus_ext_id = int(r.set_bonus.external_id)
            equipped = int(bonus_counts.get(bonus_ext_id, 0))

            if equipped < int(r.pieces):
                continue

            s = r.skill
            if not s:
                continue

            skill_external_id = int(getattr(s, "external_id", 0) or 0)
            level = int(getattr(r, "level", 0) or 0)
            if skill_external_id <= 0 or level <= 0:
                continue

            if skill_external_id not in best or level > int(best[skill_external_id]):
                best[skill_external_id] = level

        return best

    # ------------------------------
    # Skill aggregation (armor + charm + decoration + set_bonus)
    # ------------------------------
    def _merge_skill(
        self,
        acc: Dict[int, Dict[str, object]],
        *,
        skill: Skill,
        add_level: int,
        source_key: str,
    ) -> None:
        """
        Merge one skill contribution into the accumulator.

        IMPORTANT:
        - skill_id in the API contract = Skill.external_id (NOT internal PK).
        - We key the accumulator by Skill.external_id to match tests and API responses.
        """
        if not skill or add_level <= 0:
            return

        skill_external_id = int(getattr(skill, "external_id", 0) or 0)
        if skill_external_id <= 0:
            return

        max_level = int(getattr(skill, "max_level", 1) or 1)

        row = acc.get(skill_external_id)
        if row is None:
            row = {
                "skill_id": skill_external_id,
                "name": skill.name,
                "level": 0,
                "max_level": max_level,
                "sources": {},
            }
            acc[skill_external_id] = row

        if (row.get("name") or "") != (skill.name or ""):
            row["name"] = skill.name
        row["max_level"] = max(int(row.get("max_level") or 1), max_level)

        sources = row.get("sources") or {}
        sources[source_key] = int(sources.get(source_key, 0)) + int(add_level)
        row["sources"] = sources

        row["level"] = int(row.get("level", 0)) + int(add_level)

    def _finalize_skills(self, acc: Dict[int, Dict[str, object]]) -> List[Dict[str, object]]:
        out = []
        for _sid, row in acc.items():
            max_level = int(row.get("max_level") or 1)
            level = int(row.get("level") or 0)

            if level > max_level:
                row["level"] = max_level

            src = row.get("sources") or {}
            row["sources"] = {k: int(v) for k, v in src.items()}

            out.append(row)

        out.sort(key=lambda x: (-int(x.get("level") or 0), str(x.get("name") or "").lower()))
        return out

    def _compute_all_skills(self, build: Build) -> List[Dict[str, object]]:
        """
        Aggregate skills from:
          - ArmorSkill (equipped armor pieces)
          - CharmSkill (build.charm)
          - DecorationSkill (decorations equipped in build sockets)
          - SetBonusRank (active thresholds)

        Note:
          - Weapon skills are not modeled yet in your schema, so they are not included here.
        """
        acc: Dict[int, Dict[str, object]] = {}

        equipped_armors = self._get_equipped_armors(build)
        if equipped_armors:
            armor_ids = [a.id for a in equipped_armors if a and a.id]
            qs = ArmorSkill.objects.select_related("skill").filter(armor_id__in=armor_ids)
            for link in qs:
                if not link.skill:
                    continue
                self._merge_skill(
                    acc,
                    skill=link.skill,
                    add_level=max(1, int(getattr(link, "level", 1) or 1)),
                    source_key="armor",
                )

        if build.charm_id:
            qs = CharmSkill.objects.select_related("skill").filter(charm_id=build.charm_id)
            for link in qs:
                if not link.skill:
                    continue
                self._merge_skill(
                    acc,
                    skill=link.skill,
                    add_level=max(1, int(getattr(link, "level", 1) or 1)),
                    source_key="charm",
                )

        deco_ids = list(build.decorations.values_list("decoration_id", flat=True).distinct())
        if deco_ids:
            qs = DecorationSkill.objects.select_related("skill").filter(decoration_id__in=deco_ids)
            for link in qs:
                if not link.skill:
                    continue
                self._merge_skill(
                    acc,
                    skill=link.skill,
                    add_level=max(1, int(getattr(link, "level", 1) or 1)),
                    source_key="decoration",
                )

        contribs = self._compute_set_bonus_skill_contribs(build)  # {skill_external_id: lvl}
        if contribs:
            # Lookup by external_id (NOT internal PK)
            qs = Skill.objects.filter(external_id__in=list(contribs.keys()))
            by_external = {int(s.external_id): s for s in qs}

            for skill_external_id, lvl in contribs.items():
                s = by_external.get(int(skill_external_id))
                if not s:
                    continue
                self._merge_skill(
                    acc,
                    skill=s,
                    add_level=max(1, int(lvl)),
                    source_key="set_bonus",
                )

        return self._finalize_skills(acc)

    # ------------------------------
    # Endpoint
    # ------------------------------
    def get(self, request, *args, **kwargs):
        build = self.get_object()

        # Weapon integration (attack/affinity/element)
        attack, affinity, element = self._compute_weapon_stats(build)

        set_bonuses = self._compute_set_bonuses(build)
        defense = self._compute_defense(build)
        resistances = self._compute_resistances(build)

        data = {
            "build_id": build.id,
            "stats": {
                "attack": attack,
                "affinity": affinity,
                "element": element,
                "defense": defense,
                "resistances": resistances,
            },
            "skills": self._compute_all_skills(build),
            "set_bonuses": set_bonuses,
        }

        serializer = BuildStatsSerializer(instance=data)
        return Response(serializer.data)