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
)


# ==================================================
# Monsters
# ==================================================
class MonsterWeaknessSerializer(serializers.ModelSerializer):
    """
    Serializer for a monster weakness entry.
    """
    class Meta:
        model = MonsterWeakness
        fields = ["kind", "name", "stars", "condition"]


class MonsterListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list endpoints.
    """
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
    """
    Detail serializer includes nested weaknesses.
    """
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
    """
    Weapon list serializer (MVP).
    """
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
    """
    Weapon detail serializer (MVP).
    """
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
    """
    Skill list serializer (MVP).
    Notes:
    - Must include description because tests expect it.
    """
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
    """
    Skill detail serializer (MVP).
    """
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
    """
    Serializer for an armor-skill join entry.
    Includes:
    - skill (nested minimal info)
    - level
    """
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


class ArmorListSerializer(serializers.ModelSerializer):
    """
    Armor list serializer (MVP).
    """
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
    """
    Armor detail serializer (MVP).
    Includes nested skills with levels via ArmorSkill.
    """
    armor_skills = ArmorSkillEntrySerializer(many=True, read_only=True)

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
        ]


# ==================================================
# Builds
# ==================================================
class BuildArmorPieceSerializer(serializers.ModelSerializer):
    """
    Read:
    - slot
    - armor (minimal)
    Write:
    - armor_id
    """
    armor = serializers.SerializerMethodField(read_only=True)
    armor_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = BuildArmorPiece
        fields = [
            "slot",
            "armor",
            "armor_id",
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
    """
    Build list serializer (MVP).
    """
    weapon = serializers.SerializerMethodField()

    class Meta:
        model = Build
        fields = [
            "id",
            "name",
            "description",
            "weapon",
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
    """
    Build detail serializer (MVP).
    """
    weapon = serializers.SerializerMethodField()
    armor_pieces = BuildArmorPieceSerializer(many=True, read_only=True)

    class Meta:
        model = Build
        fields = [
            "id",
            "name",
            "description",
            "weapon",
            "armor_pieces",
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
    Build create/update serializer (MVP).
    - armor_pieces uses replace semantics
    """
    weapon_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    armor_pieces = BuildArmorPieceSerializer(many=True, required=False)

    class Meta:
        model = Build
        fields = [
            "id",
            "name",
            "description",
            "weapon_id",
            "armor_pieces",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        armor_pieces_data = validated_data.pop("armor_pieces", [])
        weapon_id = validated_data.pop("weapon_id", None)

        build = Build.objects.create(
            weapon_id=weapon_id,
            **validated_data,
        )

        for p in armor_pieces_data:
            slot = p.get("slot")
            armor_id = p.get("armor_id")
            if slot and armor_id:
                BuildArmorPiece.objects.create(
                    build=build,
                    slot=slot,
                    armor_id=armor_id,
                )

        return build

    def update(self, instance, validated_data):
        armor_pieces_data = validated_data.pop("armor_pieces", None)
        weapon_id = validated_data.pop("weapon_id", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)

        if "weapon_id" in self.initial_data:
            instance.weapon_id = weapon_id

        instance.save()

        if armor_pieces_data is not None:
            BuildArmorPiece.objects.filter(build=instance).delete()
            for p in armor_pieces_data:
                slot = p.get("slot")
                armor_id = p.get("armor_id")
                if slot and armor_id:
                    BuildArmorPiece.objects.create(
                        build=instance,
                        slot=slot,
                        armor_id=armor_id,
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
        help_text="Breakdown of skill levels by source (armor/charm/decoration/weapon/set_bonus)"
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

