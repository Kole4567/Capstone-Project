from django.db import models


class Monster(models.Model):
    # ID from external data source (e.g. mhw-db)
    external_id = models.IntegerField(unique=True, null=True, blank=True)

    # Monster name
    name = models.CharField(max_length=120)

    # Monster classification (e.g. Fanged Wyvern, Elder Dragon)
    monster_type = models.CharField(max_length=80)

    # Whether the monster is an Elder Dragon
    is_elder_dragon = models.BooleanField(default=False)

    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MonsterWeakness(models.Model):
    # Reference to the related monster
    monster = models.ForeignKey(
        Monster,
        on_delete=models.CASCADE,
        related_name="weaknesses",
    )

    # Weakness category (e.g. element, ailment)
    kind = models.CharField(max_length=40)

    # Weakness name (e.g. Fire, Water, Poison)
    name = models.CharField(max_length=60)

    # Effectiveness level (usually represented as stars, e.g. 1–3)
    stars = models.PositiveSmallIntegerField()

    # Optional condition describing when the weakness applies
    condition = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        # Prevent duplicate weaknesses for the same monster
        unique_together = ("monster", "kind", "name", "condition")

    def __str__(self):
        return f"{self.monster.name} - {self.kind}:{self.name} ({self.stars})"