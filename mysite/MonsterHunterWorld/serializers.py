from rest_framework import serializers
from MonsterHunterWorld.models import Monster, MonsterWeakness


class MonsterWeaknessSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonsterWeakness
        fields = ["kind", "name", "stars", "condition"]


class MonsterListSerializer(serializers.ModelSerializer):
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