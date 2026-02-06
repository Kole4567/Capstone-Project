from rest_framework import serializers

from MonsterHunterWorld.models import Monster, MonsterWeakness, Weapon, Skill


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
    Must include description because tests expect it.
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