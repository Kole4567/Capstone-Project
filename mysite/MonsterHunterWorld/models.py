from django.db import models
from django.db.models import Q


class Monster(models.Model):
    """
    Monster model (core entity).

    Notes
    - external_id is the stable identifier from the external source (mhw-db).
    - We treat external_id as required and unique so re-imports can reliably "upsert".
    - If external_id were nullable, multiple NULL rows could exist depending on DB behavior,
      which can break the assumption that external_id uniquely identifies a monster.
    """

    # Stable ID from external data source (e.g., mhw-db).
    # Required + unique enables reliable upsert by external_id on re-imports.
    external_id = models.IntegerField(unique=True)

    # Monster name (e.g., Rathalos)
    name = models.CharField(max_length=120)

    # Monster classification (e.g., Flying Wyvern, Elder Dragon)
    monster_type = models.CharField(max_length=80)

    # Whether the monster is an Elder Dragon
    is_elder_dragon = models.BooleanField(default=False)

    # Timestamp fields (useful for debugging, audits, and future sync logic)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MonsterWeakness(models.Model):
    """
    Represents a monster’s elemental or status weakness.

    Route B design (condition matters)
    - Condition can be meaningful game information (e.g., only when enraged),
      so we allow multiple rows for the same (monster, kind, name) as long as the
      condition differs.
    - To avoid "string mismatch duplicates" (extra spaces / casing / punctuation),
      we store:
        * condition      : the original display string
        * condition_key  : a normalized version used for uniqueness and filtering

    Safety
    - Stars are constrained at the database level to the valid domain (1–3).
    """

    # Reference to the related monster.
    # CASCADE delete ensures weaknesses are removed automatically when a monster is deleted.
    monster = models.ForeignKey(
        Monster,
        on_delete=models.CASCADE,
        related_name="weaknesses",
    )

    # Weakness category (e.g. "element", "ailment")
    kind = models.CharField(max_length=40)

    # Weakness name (e.g. Fire, Water, Poison)
    name = models.CharField(max_length=60)

    # Effectiveness level (usually represented as stars, e.g. 1–3)
    # PositiveSmallIntegerField prevents negative values.
    stars = models.PositiveSmallIntegerField()

    # Optional condition describing when the weakness applies
    # Keep the original text for display / UX.
    condition = models.CharField(max_length=200, null=True, blank=True)

    # Normalized condition used for deduplication / stable uniqueness checks.
    # Example: " Only when enraged " -> "only when enraged"
    # Null/blank condition becomes empty string in condition_key.
    condition_key = models.CharField(max_length=200, default="", blank=True)

    def save(self, *args, **kwargs):
        """
        Keep condition_key in sync with condition.

        Normalization policy:
        - None -> ""
        - strip outer whitespace
        - collapse internal whitespace to single spaces (optional, but recommended)
        - lowercase

        This prevents near-duplicate rows caused by minor string variations.
        """
        raw = self.condition or ""
        # Basic normalization: strip + lowercase
        normalized = " ".join(raw.split()).strip().lower()
        self.condition_key = normalized
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            # Route B uniqueness: allow different conditions as separate rows,
            # but still prevent duplicates for the same normalized condition.
            models.UniqueConstraint(
                fields=["monster", "kind", "name", "condition_key"],
                name="uniq_monsterweakness_monster_kind_name_conditionkey",
            ),
            # Enforce valid star range at the DB level (last line of defense)
            models.CheckConstraint(
                condition=Q(stars__gte=1) & Q(stars__lte=3),
                name="chk_monsterweakness_stars_1_3",
            ),
        ]

        # Helpful indexes for common query patterns:
        # - filtering monsters by weakness kind
        # - filtering by element name
        # - filtering by condition (normalized)
        indexes = [
            models.Index(fields=["monster", "kind"], name="idx_weak_monster_kind"),
            models.Index(fields=["kind", "name"], name="idx_weak_kind_name"),
            models.Index(fields=["condition_key"], name="idx_weak_condition_key"),
        ]

    def __str__(self):
        # Show condition when present for better debugging/readability.
        if self.condition:
            return f"{self.monster.name} - {self.kind}:{self.name} ({self.stars}) [{self.condition}]"
        return f"{self.monster.name} - {self.kind}:{self.name} ({self.stars})"