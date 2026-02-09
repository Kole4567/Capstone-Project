from rest_framework import serializers

from MonsterHunterWorld.models import (
    Monster,
    MonsterWeakness,
    Weapon,
    Skill,
    Armor,
    ArmorSkill,
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

    Notes
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
    - level (the armor-provided level for that skill)
    """
    # Keep this minimal to avoid large payloads.
    # (SkillListSerializer includes description; for armor detail we only need name/id/max_level.)
    skill = serializers.SerializerMethodField()

    class Meta:
        model = ArmorSkill
        fields = [
            "skill",
            "level",
        ]

    def get_skill(self, obj):
        """
        Return a minimal nested skill object to keep armor detail responses small.
        """
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

    Notes
    - Keep list lightweight; include key identity + defense + slots.
    - Skills are omitted in list to keep payload small.
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