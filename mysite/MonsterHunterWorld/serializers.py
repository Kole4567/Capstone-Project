from rest_framework import serializers

from MonsterHunterWorld.models import (
    Monster,
    MonsterWeakness,
    Weapon,
    Skill,
    Armor,
    ArmorSkill,
    Build,
    BuildArmorPiece,
    Charm,
    CharmSkill,
    Decoration,
    DecorationSkill,
    BuildDecoration,
)


# ==================================================
# Monsters
# ==================================================
class MonsterWeaknessSerializer(serializers.ModelSerializer):
    """Serializer for a monster weakness entry."""

    class Meta:
        model = MonsterWeakness
        fields = ["kind", "name", "stars", "condition"]


class MonsterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list endpoints."""

    class Meta:
        model = Monster
        fields = [
            "id",
            "external_id",
            "name",
            "monster_type",
            "is_elder_dragon",
        ]


class MonsterDetailSerializer(serializers.ModelSerializer):
    """Detail serializer includes nested weaknesses."""

    weaknesses = MonsterWeaknessSerializer(many=True, read_only=True)

    class Meta:
        model = Monster
        fields = [
            "id",
            "external_id",
            "name",
            "monster_type",
            "is_elder_dragon",
            "weaknesses",
        ]


# ==================================================
# Weapons
# ==================================================
class WeaponListSerializer(serializers.ModelSerializer):
    """Weapon list serializer (MVP)."""

    class Meta:
        model = Weapon
        fields = [
            "id",
            "external_id",
            "name",
            "weapon_type",
            "rarity",
            "attack_display",
            "attack_raw",
            "element",
            "element_damage",
            "affinity",
            "elderseal",
        ]


class WeaponDetailSerializer(serializers.ModelSerializer):
    """Weapon detail serializer (MVP)."""

    class Meta:
        model = Weapon
        fields = [
            "id",
            "external_id",
            "name",
            "weapon_type",
            "rarity",
            "attack_display",
            "attack_raw",
            "element",
            "element_damage",
            "affinity",
            "elderseal",
        ]


# ==================================================
# Skills
# ==================================================
class SkillListSerializer(serializers.ModelSerializer):
    """Skill list serializer (MVP)."""

    class Meta:
        model = Skill
        fields = [
            "id",
            "external_id",
            "name",
            "description",
            "max_level",
        ]


class SkillDetailSerializer(serializers.ModelSerializer):
    """Skill detail serializer (MVP)."""

    class Meta:
        model = Skill
        fields = [
            "id",
            "external_id",
            "name",
            "description",
            "max_level",
        ]


# ==================================================
# Armor
# ==================================================
class ArmorSkillEntrySerializer(serializers.ModelSerializer):
    """Serializer for an armor-skill join entry."""

    skill = serializers.SerializerMethodField()

    class Meta:
        model = ArmorSkill
        fields = [
            "skill",
            "level",
        ]

    def get_skill(self, obj):
        if not obj.skill_id:
            return None
        return {
            "id": obj.skill.id,
            "external_id": obj.skill.external_id,
            "name": obj.skill.name,
            "max_level": obj.skill.max_level,
        }


class ArmorSetSerializer(serializers.Serializer):
    """Lightweight armor set representation stored on Armor."""

    external_id = serializers.IntegerField(allow_null=True, required=False)
    name = serializers.CharField(allow_null=True, required=False)
    rank = serializers.CharField(allow_null=True, required=False)
    bonus_external_id = serializers.IntegerField(allow_null=True, required=False)


class ArmorListSerializer(serializers.ModelSerializer):
    """Armor list serializer (MVP)."""

    class Meta:
        model = Armor
        fields = [
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
        ]


class ArmorDetailSerializer(serializers.ModelSerializer):
    """Armor detail serializer (MVP)."""

    armor_skills = ArmorSkillEntrySerializer(many=True, read_only=True)
    armor_set = serializers.SerializerMethodField()

    class Meta:
        model = Armor
        fields = [
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
            "armor_skills",
            "armor_set",
        ]

    def get_armor_set(self, obj):
        return {
            "external_id": getattr(obj, "armor_set_external_id", None),
            "name": getattr(obj, "armor_set_name", None),
            "rank": getattr(obj, "armor_set_rank", None),
            "bonus_external_id": getattr(obj, "armor_set_bonus_external_id", None),
        }


# ==================================================
# Charms
# ==================================================
class CharmSkillEntrySerializer(serializers.ModelSerializer):
    """Serializer for a charm-skill join entry."""

    skill = serializers.SerializerMethodField()

    class Meta:
        model = CharmSkill
        fields = ["skill", "level"]

    def get_skill(self, obj):
        if not obj.skill_id:
            return None
        return {
            "id": obj.skill.id,
            "external_id": obj.skill.external_id,
            "name": obj.skill.name,
            "max_level": obj.skill.max_level,
        }


class CharmListSerializer(serializers.ModelSerializer):
    """Charm list serializer (MVP)."""

    class Meta:
        model = Charm
        fields = [
            "id",
            "external_id",
            "name",
            "rarity",
        ]


class CharmDetailSerializer(serializers.ModelSerializer):
    """Charm detail serializer (MVP)."""

    charm_skills = serializers.SerializerMethodField()

    class Meta:
        model = Charm
        fields = [
            "id",
            "external_id",
            "name",
            "rarity",
            "charm_skills",
        ]

    def get_charm_skills(self, obj):
        out = []
        for cs in obj.charm_skills.select_related("skill").all():
            out.append(
                {
                    "skill": {
                        "id": cs.skill.id,
                        "external_id": cs.skill.external_id,
                        "name": cs.skill.name,
                        "max_level": cs.skill.max_level,
                    },
                    "level": cs.level,
                }
            )
        return out


class CharmMiniSerializer(serializers.ModelSerializer):
    """Minimal charm representation for embedding inside Build responses."""

    class Meta:
        model = Charm
        fields = [
            "id",
            "external_id",
            "name",
            "rarity",
        ]


# ==================================================
# Decorations
# ==================================================
class DecorationSkillEntrySerializer(serializers.ModelSerializer):
    """Serializer for a decoration-skill join entry."""

    skill = serializers.SerializerMethodField()

    class Meta:
        model = DecorationSkill
        fields = [
            "skill",
            "level",
        ]

    def get_skill(self, obj):
        if not obj.skill_id:
            return None
        return {
            "id": obj.skill.id,
            "external_id": obj.skill.external_id,
            "name": obj.skill.name,
            "max_level": obj.skill.max_level,
        }


class DecorationListSerializer(serializers.ModelSerializer):
    """Decoration list serializer (MVP)."""

    class Meta:
        model = Decoration
        fields = [
            "id",
            "external_id",
            "name",
            "rarity",
        ]


class DecorationDetailSerializer(serializers.ModelSerializer):
    """Decoration detail serializer (MVP)."""

    decoration_skills = DecorationSkillEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Decoration
        fields = [
            "id",
            "external_id",
            "name",
            "rarity",
            "decoration_skills",
        ]


class BuildDecorationSerializer(serializers.ModelSerializer):
    """
    Read:
    - slot
    - socket_index
    - decoration (minimal)

    Write options (either is OK):
    - decoration_id (internal PK)
    - decoration_external_id (mhw-db id)
    """

    decoration = serializers.SerializerMethodField(read_only=True)

    decoration_id = serializers.IntegerField(write_only=True, required=False)
    decoration_external_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = BuildDecoration
        fields = [
            "slot",
            "socket_index",
            "decoration",
            "decoration_id",
            "decoration_external_id",
        ]

    def get_decoration(self, obj):
        if not obj.decoration_id:
            return None
        return {
            "id": obj.decoration.id,
            "external_id": obj.decoration.external_id,
            "name": obj.decoration.name,
            "rarity": obj.decoration.rarity,
        }


# ==================================================
# Builds
# ==================================================
class BuildArmorPieceSerializer(serializers.ModelSerializer):
    """
    Read:
    - slot
    - armor (minimal)

    Write options (either is OK):
    - armor_id (internal PK)
    - armor_external_id (mhw-db id)
    """

    armor = serializers.SerializerMethodField(read_only=True)

    armor_id = serializers.IntegerField(write_only=True, required=False)
    armor_external_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = BuildArmorPiece
        fields = [
            "slot",
            "armor",
            "armor_id",
            "armor_external_id",
        ]

    def get_armor(self, obj):
        if not obj.armor_id:
            return None
        return {
            "id": obj.armor.id,
            "external_id": obj.armor.external_id,
            "name": obj.armor.name,
            "armor_type": obj.armor.armor_type,
            "rarity": obj.armor.rarity,
            "defense_base": obj.armor.defense_base,
            "slot_1": obj.armor.slot_1,
            "slot_2": obj.armor.slot_2,
            "slot_3": obj.armor.slot_3,
        }


class BuildListSerializer(serializers.ModelSerializer):
    """Build list serializer (MVP)."""

    weapon = serializers.SerializerMethodField()
    charm = CharmMiniSerializer(read_only=True)

    class Meta:
        model = Build
        fields = [
            "id",
            "name",
            "description",
            "weapon",
            "charm",
            "created_at",
            "updated_at",
        ]

    def get_weapon(self, obj):
        if not obj.weapon_id:
            return None
        return {
            "id": obj.weapon.id,
            "external_id": obj.weapon.external_id,
            "name": obj.weapon.name,
            "weapon_type": obj.weapon.weapon_type,
            "rarity": obj.weapon.rarity,
        }


class BuildDetailSerializer(serializers.ModelSerializer):
    """Build detail serializer (MVP)."""

    weapon = serializers.SerializerMethodField()
    charm = CharmMiniSerializer(read_only=True)
    armor_pieces = BuildArmorPieceSerializer(many=True, read_only=True)
    decorations = BuildDecorationSerializer(many=True, read_only=True)

    class Meta:
        model = Build
        fields = [
            "id",
            "name",
            "description",
            "weapon",
            "charm",
            "armor_pieces",
            "decorations",
            "created_at",
            "updated_at",
        ]

    def get_weapon(self, obj):
        if not obj.weapon_id:
            return None
        return {
            "id": obj.weapon.id,
            "external_id": obj.weapon.external_id,
            "name": obj.weapon.name,
            "weapon_type": obj.weapon.weapon_type,
            "rarity": obj.weapon.rarity,
            "attack_raw": obj.weapon.attack_raw,
            "attack_display": obj.weapon.attack_display,
            "element": obj.weapon.element,
            "element_damage": obj.weapon.element_damage,
            "affinity": obj.weapon.affinity,
            "elderseal": obj.weapon.elderseal,
        }


class BuildCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Build create/update serializer (MHW-friendly).

    IMPORTANT PATCH FIX:
    - We ONLY replace armor pieces / decorations when the corresponding key is present
      in the request payload (self.initial_data). This prevents accidental wiping when
      PATCHing only weapon_id/charm_id.

    Supported write payload styles:

    (A) Current style (internal PK):
      "armor_pieces": [{"slot":"head","armor_id":3360}, ...]
      "decorations": [{"slot":"head","socket_index":1,"decoration_id":123}, ...]

    (B) MHW-style (external_id):
      "armors": {"head": 6, "chest": 7, "gloves": 8, "waist": 9, "legs": 10}
      "decorations": [{"slot":"head","socket_index":1,"decoration_external_id":5}, ...]
    """

    # Write-only inputs
    weapon_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    charm_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    weapon_external_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    charm_external_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    # MHW-style dict: slot -> Armor.external_id
    armors = serializers.DictField(
        child=serializers.IntegerField(),
        required=False,
        help_text='Example: {"head": 6, "chest": 7, "gloves": 8, "waist": 9, "legs": 10}',
    )

    # Nested lists (read + optional write)
    armor_pieces = BuildArmorPieceSerializer(many=True, required=False)
    decorations = BuildDecorationSerializer(many=True, required=False)

    # Read-only embeds (so PATCH response is MHW-friendly)
    weapon = serializers.SerializerMethodField(read_only=True)
    charm = CharmMiniSerializer(read_only=True)

    class Meta:
        model = Build
        fields = [
            "id",
            "name",
            "description",
            "weapon",
            "charm",
            "weapon_id",
            "charm_id",
            "weapon_external_id",
            "charm_external_id",
            "armors",
            "armor_pieces",
            "decorations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_weapon(self, obj):
        if not obj.weapon_id:
            return None
        return {
            "id": obj.weapon.id,
            "external_id": obj.weapon.external_id,
            "name": obj.weapon.name,
            "weapon_type": obj.weapon.weapon_type,
            "rarity": obj.weapon.rarity,
            "attack_raw": obj.weapon.attack_raw,
            "attack_display": obj.weapon.attack_display,
            "element": obj.weapon.element,
            "element_damage": obj.weapon.element_damage,
            "affinity": obj.weapon.affinity,
            "elderseal": obj.weapon.elderseal,
        }

    # ------------------------------
    # Validation helpers
    # ------------------------------
    VALID_ARMOR_SLOTS = {"head", "chest", "gloves", "waist", "legs"}
    VALID_DECO_SLOTS = {"head", "chest", "gloves", "waist", "legs", "weapon"}

    def _normalize_slot(self, s: str) -> str:
        return (s or "").strip().lower()

    def _build_armor_map_from_armors_dict(self, armors_dict):
        """
        Convert {"head": 6, ...} (external_id) to a list of (slot, armor_internal_id).
        Also validates armor_type matches slot.
        """
        if not isinstance(armors_dict, dict):
            raise serializers.ValidationError({"armors": "must be an object (dict)."})

        slot_to_ext = {}
        for raw_slot, raw_ext_id in armors_dict.items():
            slot = self._normalize_slot(raw_slot)
            if slot not in self.VALID_ARMOR_SLOTS:
                raise serializers.ValidationError({"armors": f"invalid slot: {raw_slot}"})
            try:
                ext_id = int(raw_ext_id)
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    {"armors": f"invalid external_id for {raw_slot}: {raw_ext_id}"}
                )
            slot_to_ext[slot] = ext_id

        if not slot_to_ext:
            return []

        ext_ids = list(slot_to_ext.values())
        armors = Armor.objects.filter(external_id__in=ext_ids)
        by_external = {int(a.external_id): a for a in armors}

        missing = [eid for eid in ext_ids if int(eid) not in by_external]
        if missing:
            raise serializers.ValidationError({"armors": f"armor_external_id not found: {missing}"})

        out = []
        for slot, ext_id in slot_to_ext.items():
            armor = by_external[int(ext_id)]
            if (armor.armor_type or "").strip().lower() != slot:
                raise serializers.ValidationError(
                    {
                        "armors": (
                            f"armor_type mismatch: slot '{slot}' requires armor_type '{slot}', "
                            f"got '{armor.armor_type}' (external_id={ext_id})"
                        )
                    }
                )
            out.append((slot, armor.id))

        return out

    def _resolve_weapon_ids(self, validated_data):
        """Resolve weapon_id via either internal PK or external_id."""
        if "weapon_id" in validated_data:
            return validated_data.pop("weapon_id")

        if "weapon_external_id" in validated_data:
            ext = validated_data.pop("weapon_external_id")
            if ext is None:
                return None
            w = Weapon.objects.filter(external_id=int(ext)).first()
            if not w:
                raise serializers.ValidationError({"weapon_external_id": f"not found: {ext}"})
            return w.id

        return None

    def _resolve_charm_ids(self, validated_data):
        """Resolve charm_id via either internal PK or external_id."""
        if "charm_id" in validated_data:
            return validated_data.pop("charm_id")

        if "charm_external_id" in validated_data:
            ext = validated_data.pop("charm_external_id")
            if ext is None:
                return None
            c = Charm.objects.filter(external_id=int(ext)).first()
            if not c:
                raise serializers.ValidationError({"charm_external_id": f"not found: {ext}"})
            return c.id

        return None

    def _normalize_armor_pieces_payload(self, armor_pieces_data):
        """
        Convert armor_pieces entries that may contain armor_id OR armor_external_id.
        Validate armor exists and armor_type matches slot.
        Return list of (slot, armor_id).
        """
        if not isinstance(armor_pieces_data, list):
            raise serializers.ValidationError({"armor_pieces": "must be a list."})

        out = []
        armor_ids_to_fetch = []
        armor_exts_to_fetch = []

        for p in armor_pieces_data:
            slot = self._normalize_slot((p or {}).get("slot"))
            if slot not in self.VALID_ARMOR_SLOTS:
                raise serializers.ValidationError({"armor_pieces": f"invalid slot: {slot}"})

            armor_id = (p or {}).get("armor_id")
            armor_external_id = (p or {}).get("armor_external_id")

            if armor_id is None and armor_external_id is None:
                raise serializers.ValidationError(
                    {"armor_pieces": f"missing armor_id/armor_external_id for slot {slot}"}
                )

            if armor_id is not None:
                try:
                    armor_id = int(armor_id)
                except (TypeError, ValueError):
                    raise serializers.ValidationError(
                        {"armor_pieces": f"invalid armor_id for {slot}: {armor_id}"}
                    )
                armor_ids_to_fetch.append(armor_id)

            if armor_external_id is not None:
                try:
                    armor_external_id = int(armor_external_id)
                except (TypeError, ValueError):
                    raise serializers.ValidationError(
                        {"armor_pieces": f"invalid armor_external_id for {slot}: {armor_external_id}"}
                    )
                armor_exts_to_fetch.append(armor_external_id)

            out.append((slot, armor_id, armor_external_id))

        by_id = {}
        if armor_ids_to_fetch:
            qs = Armor.objects.filter(id__in=list(set(armor_ids_to_fetch)))
            by_id = {int(a.id): a for a in qs}

        by_ext = {}
        if armor_exts_to_fetch:
            qs = Armor.objects.filter(external_id__in=list(set(armor_exts_to_fetch)))
            by_ext = {int(a.external_id): a for a in qs}

        resolved = []
        missing_internal = []
        missing_external = []

        for slot, armor_id, armor_external_id in out:
            armor = None

            if armor_id is not None:
                armor = by_id.get(int(armor_id))
                if not armor:
                    missing_internal.append(int(armor_id))

            if armor is None and armor_external_id is not None:
                armor = by_ext.get(int(armor_external_id))
                if not armor:
                    missing_external.append(int(armor_external_id))

            if armor is None:
                raise serializers.ValidationError(
                    {
                        "armor_pieces": (
                            f"armor not found (armor_id={armor_id}, armor_external_id={armor_external_id})"
                        )
                    }
                )

            if (armor.armor_type or "").strip().lower() != slot:
                raise serializers.ValidationError(
                    {
                        "armor_pieces": (
                            f"armor_type mismatch: slot '{slot}' requires armor_type '{slot}', "
                            f"got '{armor.armor_type}'"
                        )
                    }
                )

            resolved.append((slot, int(armor.id)))

        if missing_internal:
            raise serializers.ValidationError(
                {"armor_pieces": f"armor_id not found: {sorted(set(missing_internal))}"}
            )
        if missing_external:
            raise serializers.ValidationError(
                {"armor_pieces": f"armor_external_id not found: {sorted(set(missing_external))}"}
            )

        return resolved

    def _normalize_decorations_payload(self, decorations_data):
        """
        Convert decorations entries that may contain decoration_id OR decoration_external_id.
        Validate slot + socket_index + decoration exists.
        Return list of (slot, socket_index, decoration_id).
        """
        if decorations_data is None:
            return None

        if not isinstance(decorations_data, list):
            raise serializers.ValidationError({"decorations": "must be a list."})

        deco_ids = []
        deco_exts = []
        cleaned = []

        for d in decorations_data:
            slot = self._normalize_slot((d or {}).get("slot"))
            if slot not in self.VALID_DECO_SLOTS:
                raise serializers.ValidationError({"decorations": f"invalid slot: {slot}"})

            try:
                socket_index = int((d or {}).get("socket_index"))
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    {"decorations": f"invalid socket_index for slot {slot}"}
                )

            if socket_index < 1 or socket_index > 3:
                raise serializers.ValidationError({"decorations": "socket_index must be 1..3"})

            decoration_id = (d or {}).get("decoration_id")
            decoration_external_id = (d or {}).get("decoration_external_id")

            if decoration_id is None and decoration_external_id is None:
                raise serializers.ValidationError({"decorations": "missing decoration_id/decoration_external_id"})

            if decoration_id is not None:
                try:
                    decoration_id = int(decoration_id)
                except (TypeError, ValueError):
                    raise serializers.ValidationError({"decorations": f"invalid decoration_id: {decoration_id}"})
                deco_ids.append(decoration_id)

            if decoration_external_id is not None:
                try:
                    decoration_external_id = int(decoration_external_id)
                except (TypeError, ValueError):
                    raise serializers.ValidationError(
                        {"decorations": f"invalid decoration_external_id: {decoration_external_id}"}
                    )
                deco_exts.append(decoration_external_id)

            cleaned.append((slot, socket_index, decoration_id, decoration_external_id))

        by_id = {}
        if deco_ids:
            qs = Decoration.objects.filter(id__in=list(set(deco_ids)))
            by_id = {int(x.id): x for x in qs}

        by_ext = {}
        if deco_exts:
            qs = Decoration.objects.filter(external_id__in=list(set(deco_exts)))
            by_ext = {int(x.external_id): x for x in qs}

        resolved = []
        missing_internal = []
        missing_external = []

        for slot, socket_index, decoration_id, decoration_external_id in cleaned:
            deco = None

            if decoration_id is not None:
                deco = by_id.get(int(decoration_id))
                if not deco:
                    missing_internal.append(int(decoration_id))

            if deco is None and decoration_external_id is not None:
                deco = by_ext.get(int(decoration_external_id))
                if not deco:
                    missing_external.append(int(decoration_external_id))

            if deco is None:
                raise serializers.ValidationError(
                    {
                        "decorations": (
                            f"decoration not found (decoration_id={decoration_id}, "
                            f"decoration_external_id={decoration_external_id})"
                        )
                    }
                )

            resolved.append((slot, int(socket_index), int(deco.id)))

        if missing_internal:
            raise serializers.ValidationError(
                {"decorations": f"decoration_id not found: {sorted(set(missing_internal))}"}
            )
        if missing_external:
            raise serializers.ValidationError(
                {"decorations": f"decoration_external_id not found: {sorted(set(missing_external))}"}
            )

        return resolved

    # ------------------------------
    # Create / Update
    # ------------------------------
    def create(self, validated_data):
        armor_pieces_data = validated_data.pop("armor_pieces", [])
        decorations_data = validated_data.pop("decorations", [])
        armors_dict = validated_data.pop("armors", None)

        weapon_id = self._resolve_weapon_ids(validated_data)
        charm_id = self._resolve_charm_ids(validated_data)

        build = Build.objects.create(
            weapon_id=weapon_id,
            charm_id=charm_id,
            **validated_data,
        )

        # If "armors" dict is provided, it overrides armor_pieces
        if armors_dict is not None:
            pairs = self._build_armor_map_from_armors_dict(armors_dict)
            for slot, armor_id in pairs:
                BuildArmorPiece.objects.create(build=build, slot=slot, armor_id=armor_id)
        else:
            pairs = self._normalize_armor_pieces_payload(armor_pieces_data) if armor_pieces_data else []
            for slot, armor_id in pairs:
                BuildArmorPiece.objects.create(build=build, slot=slot, armor_id=armor_id)

        decos = self._normalize_decorations_payload(decorations_data) if decorations_data else []
        for slot, socket_index, decoration_id in decos:
            BuildDecoration.objects.create(
                build=build,
                slot=slot,
                socket_index=socket_index,
                decoration_id=decoration_id,
            )

        return build

    def update(self, instance, validated_data):
        # Pop nested fields first (they might exist in validated_data even if not sent on PATCH)
        armor_pieces_data = validated_data.pop("armor_pieces", None)
        decorations_data = validated_data.pop("decorations", None)
        armors_dict = validated_data.pop("armors", None)

        # Track which keys were actually sent by the client
        has_armors = "armors" in self.initial_data
        has_armor_pieces = "armor_pieces" in self.initial_data
        has_decorations = "decorations" in self.initial_data
        has_weapon = ("weapon_id" in self.initial_data) or ("weapon_external_id" in self.initial_data)
        has_charm = ("charm_id" in self.initial_data) or ("charm_external_id" in self.initial_data)

        # Update basic scalar fields (name/description/etc.)
        for k, v in validated_data.items():
            setattr(instance, k, v)

        # Weapon/charm resolution must happen BEFORE saving
        if has_weapon:
            weapon_id = self._resolve_weapon_ids(validated_data)
            instance.weapon_id = weapon_id

        if has_charm:
            charm_id = self._resolve_charm_ids(validated_data)
            instance.charm_id = charm_id

        instance.save()

        # Armor replace semantics ONLY if client sent "armors" or "armor_pieces"
        if has_armors:
            BuildArmorPiece.objects.filter(build=instance).delete()
            pairs = self._build_armor_map_from_armors_dict(armors_dict or {})
            for slot, armor_id in pairs:
                BuildArmorPiece.objects.create(build=instance, slot=slot, armor_id=armor_id)

        elif has_armor_pieces:
            BuildArmorPiece.objects.filter(build=instance).delete()
            pairs = self._normalize_armor_pieces_payload(armor_pieces_data or [])
            for slot, armor_id in pairs:
                BuildArmorPiece.objects.create(build=instance, slot=slot, armor_id=armor_id)

        # Decorations replace semantics ONLY if client sent "decorations"
        if has_decorations:
            BuildDecoration.objects.filter(build=instance).delete()
            decos = self._normalize_decorations_payload(decorations_data or []) or []
            for slot, socket_index, decoration_id in decos:
                BuildDecoration.objects.create(
                    build=instance,
                    slot=slot,
                    socket_index=socket_index,
                    decoration_id=decoration_id,
                )

        return instance


# ==================================================
# Build Stats (MHW-style Contract)
# ==================================================
class BuildComputedSkillSerializer(serializers.Serializer):
    skill_id = serializers.IntegerField()
    name = serializers.CharField()
    level = serializers.IntegerField()
    max_level = serializers.IntegerField()

    sources = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Breakdown of skill levels by source (armor/charm/decoration/weapon/set_bonus)",
    )


class BuildAttackSerializer(serializers.Serializer):
    raw = serializers.IntegerField()
    display = serializers.IntegerField()


class BuildElementSerializer(serializers.Serializer):
    type = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    value = serializers.IntegerField()


class BuildResistancesSerializer(serializers.Serializer):
    fire = serializers.IntegerField()
    water = serializers.IntegerField()
    thunder = serializers.IntegerField()
    ice = serializers.IntegerField()
    dragon = serializers.IntegerField()


class BuildStatsBlockSerializer(serializers.Serializer):
    attack = BuildAttackSerializer()
    affinity = serializers.IntegerField()
    element = BuildElementSerializer(allow_null=True, required=False)
    defense = serializers.IntegerField()
    resistances = BuildResistancesSerializer()


class BuildSetBonusSerializer(serializers.Serializer):
    name = serializers.CharField()
    pieces = serializers.IntegerField()
    active = serializers.BooleanField()


class BuildStatsSerializer(serializers.Serializer):
    build_id = serializers.IntegerField()
    stats = BuildStatsBlockSerializer()
    skills = BuildComputedSkillSerializer(many=True)
    set_bonuses = BuildSetBonusSerializer(many=True, required=False)