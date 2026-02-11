import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction

from MonsterHunterWorld.models import Skill, SetBonus, SetBonusRank


# ==================================================
# JSON helpers (defensive)
# ==================================================
def extract_list(payload: Any) -> List[Dict[str, Any]]:
    """
    Return a list of armor sets from various possible JSON shapes.

    Supported shapes:
      1) [ {...}, {...}, ... ]
      2) { "armorSets": [ ... ] }
      3) { "armor_sets": [ ... ] }
      4) { "data": { "armorSets": [ ... ] } }
      5) { "results": [ ... ] }
      6) { "data": [ ... ] }
    """
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if not isinstance(payload, dict):
        return []

    candidates = [
        payload.get("armorSets"),
        payload.get("armor_sets"),
        (payload.get("data") or {}).get("armorSets") if isinstance(payload.get("data"), dict) else None,
        payload.get("results"),
        payload.get("data") if isinstance(payload.get("data"), list) else None,
    ]

    for c in candidates:
        if isinstance(c, list):
            return [x for x in c if isinstance(x, dict)]

    return []


def safe_int(v: Any, default: Optional[int] = 0) -> Optional[int]:
    try:
        if v is None:
            return default
        return int(v)
    except (ValueError, TypeError):
        return default


def ensure_list(v: Any) -> List[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return [v]
    return []


def first_present(d: Dict[str, Any], keys: List[str]) -> Any:
    """Return the first non-None value among given keys."""
    for k in keys:
        if k in d and d.get(k) is not None:
            return d.get(k)
    return None


def pick_external_id(obj: Any) -> Optional[int]:
    """Try multiple keys for an external id."""
    if not isinstance(obj, dict):
        return None

    for k in ("external_id", "externalId", "id"):
        v = obj.get(k)
        if v is None:
            continue
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    return None


# ==================================================
# Normalization for ranks/skills
# ==================================================
@dataclass
class MergedRank:
    pieces: int
    skill_external_id: int
    level: int
    description: str


# Unique identity for a rank row in DB (MHW semantics)
# We include "level" because some set bonuses can grant different levels.
RankKey = Tuple[int, int, int]  # (pieces, skill_external_id, level)


def _normalize_rank(  # noqa: C901 (ok: defensive parsing)
    rank_obj: Dict[str, Any],
    *,
    skills_by_external: Dict[int, Skill],
) -> Optional[Tuple[int, int, int, str]]:
    """
    Normalize one rank entry into:
      (pieces, skill_external_id, level, description)

    We support BOTH common mhw-db shapes:

    Shape A (newer / from mhw-db /armor/sets):
      {
        "pieces": 4,
        "skill": {
          "skill": 118,          # <- Skill external id
          "skillName": "Capture Master",
          "level": 1,
          ...
        },
        "description": "..."
      }

    Shape B (seen in some cached/modified exports):
      {
        "pieces": 2,
        "skill": 118,            # <- Skill external id (int)
        "skillName": "Razor Sharp/Spare Shot",
        "level": 1,
        "description": "..."
      }

    Notes:
    - If skillName is missing, we fill from DB Skill(external_id).
    - If description is missing, keep "".
    """
    if not isinstance(rank_obj, dict):
        return None

    pieces = safe_int(first_present(rank_obj, ["pieces", "piecesRequired", "pieces_required"]), 0) or 0
    if pieces <= 0:
        return None

    desc = (first_present(rank_obj, ["description", "desc"]) or "").strip()

    raw_skill = rank_obj.get("skill")

    # Case 1: skill is a dict
    if isinstance(raw_skill, dict):
        # mhw-db nested skill dict uses "skill" as external_id
        skill_external_id = safe_int(first_present(raw_skill, ["skill", "external_id", "id"]), 0) or 0
        level = safe_int(first_present(raw_skill, ["level"]), 0) or 0
        if level <= 0:
            # sometimes level lives at the rank level
            level = safe_int(first_present(rank_obj, ["level", "skillLevel", "skill_level"]), 0) or 0

        if skill_external_id <= 0 or level <= 0:
            return None

        # We *prefer* nested description, but keep rank description as fallback
        nested_desc = (first_present(raw_skill, ["description"]) or "").strip()
        if nested_desc and (not desc or len(nested_desc) > len(desc)):
            desc = nested_desc

        # We don't need name here, but we try to validate existence if possible
        if skill_external_id not in skills_by_external:
            # Skill must exist from import_skills; if not, we still allow placeholder creation later
            pass

        return int(pieces), int(skill_external_id), int(level), desc

    # Case 2: skill is an int (external_id)
    if isinstance(raw_skill, int) or isinstance(raw_skill, str):
        skill_external_id = safe_int(raw_skill, 0) or 0
        if skill_external_id <= 0:
            return None

        level = safe_int(first_present(rank_obj, ["level", "skillLevel", "skill_level"]), 0) or 0
        if level <= 0:
            # If level is missing, safest fallback is 1 (MHW set bonus ranks are typically lvl 1)
            level = 1

        return int(pieces), int(skill_external_id), int(level), desc

    return None


# ==================================================
# Command
# ==================================================
class Command(BaseCommand):
    help = "Import MHW set bonuses from mhw-db armor sets JSON."

    def add_arguments(self, parser):
        # ----
        # Backward/forward compatible CLI options:
        # - Preferred: --armor-sets
        # - Alias:     --sets
        # Either is accepted; at least one is required.
        # ----
        parser.add_argument(
            "--armor-sets",
            dest="armor_sets",
            type=str,
            required=False,
            help="Path to mhw-db armor sets JSON file (e.g., data/mhw_armor_sets.json)",
        )
        parser.add_argument(
            "--sets",
            dest="sets",
            type=str,
            required=False,
            help="Alias for --armor-sets (compat).",
        )

        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing SetBonus/SetBonusRank rows before importing",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse only; do not write to DB (still prints stats)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of armor sets to process (0 = no limit)",
        )

    def handle(self, *args, **options):
        # Normalize path from either flag
        path = options.get("armor_sets") or options.get("sets")
        if not path:
            self.stdout.write(
                self.style.ERROR(
                    "Missing required argument: provide --armor-sets <path> (preferred) "
                    "or --sets <path> (alias)."
                )
            )
            return

        reset: bool = options["reset"]
        dry_run: bool = options["dry_run"]
        limit: int = options["limit"]

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        armor_sets = extract_list(payload)
        if not armor_sets:
            self.stdout.write(self.style.ERROR("Invalid JSON: could not find a list of armor sets"))
            return

        if limit and limit > 0:
            armor_sets = armor_sets[:limit]

        # Preload Skill objects by external_id (fast lookups)
        skills_by_external: Dict[int, Skill] = {s.external_id: s for s in Skill.objects.all()}

        # ----------------------------
        # Phase 1: scan + merge in memory
        # ----------------------------
        bonus_names: Dict[int, str] = {}
        merged: Dict[int, Dict[RankKey, MergedRank]] = {}

        scanned_sets = 0
        skipped_bonus_none = 0
        skipped_bonus_invalid = 0
        skipped_bonus_no_ranks = 0
        skipped_rank_invalid = 0

        for armor_set in armor_sets:
            scanned_sets += 1
            bonus = armor_set.get("bonus")

            if bonus is None:
                skipped_bonus_none += 1
                continue

            # Some exports store "bonus" as an int id only (no name/ranks here).
            # In that case, we cannot import ranks from this file.
            if isinstance(bonus, int):
                skipped_bonus_no_ranks += 1
                # Optional: create placeholder name if you want. But no ranks -> no usefulness for stats.
                # We'll skip to avoid polluting with incomplete data.
                continue

            if not isinstance(bonus, dict):
                skipped_bonus_invalid += 1
                continue

            bonus_id = pick_external_id(bonus)
            bonus_name = (bonus.get("name") or "").strip()

            if bonus_id is None or bonus_id <= 0:
                skipped_bonus_invalid += 1
                continue

            # If name is missing, keep a placeholder so we can still attach ranks.
            if not bonus_name:
                bonus_name = f"Set Bonus #{bonus_id}"

            bonus_names[int(bonus_id)] = bonus_name

            ranks = ensure_list(bonus.get("ranks"))
            if not ranks:
                skipped_bonus_no_ranks += 1
                continue

            if int(bonus_id) not in merged:
                merged[int(bonus_id)] = {}

            for r in ranks:
                if not isinstance(r, dict):
                    skipped_rank_invalid += 1
                    continue

                norm = _normalize_rank(r, skills_by_external=skills_by_external)
                if not norm:
                    skipped_rank_invalid += 1
                    continue

                pieces, skill_external_id, level, desc = norm

                key: RankKey = (int(pieces), int(skill_external_id), int(level))
                existing = merged[int(bonus_id)].get(key)

                # Merge strategy:
                # - keep the longer description
                if existing is None:
                    merged[int(bonus_id)][key] = MergedRank(
                        pieces=int(pieces),
                        skill_external_id=int(skill_external_id),
                        level=int(level),
                        description=desc,
                    )
                else:
                    if desc and len(desc) > len(existing.description or ""):
                        existing.description = desc

        distinct_bonuses = len(bonus_names)
        merged_rank_total = sum(len(rmap) for rmap in merged.values())

        # ----------------------------
        # Phase 2: write to DB
        # ----------------------------
        bonuses_created = 0
        bonuses_updated = 0
        ranks_created = 0
        ranks_deleted = 0
        skill_placeholders_created = 0
        skills_linked_to_ranks = 0

        if dry_run:
            self._print_stats(
                scanned_sets=scanned_sets,
                distinct_bonuses=distinct_bonuses,
                merged_rank_total=merged_rank_total,
                bonuses_created=0,
                bonuses_updated=0,
                ranks_created=0,
                ranks_deleted=0,
                skills_linked_to_ranks=0,
                skill_placeholders_created=0,
                skipped_bonus_none=skipped_bonus_none,
                skipped_bonus_invalid=skipped_bonus_invalid,
                skipped_bonus_no_ranks=skipped_bonus_no_ranks,
                skipped_rank_invalid=skipped_rank_invalid,
                dry_run=True,
            )
            return

        with transaction.atomic():
            if reset:
                SetBonusRank.objects.all().delete()
                SetBonus.objects.all().delete()

            # Upsert SetBonus, then replace ranks per bonus
            for bonus_id, bonus_name in bonus_names.items():
                bonus_obj, created = SetBonus.objects.get_or_create(
                    external_id=int(bonus_id),
                    defaults={"name": bonus_name},
                )
                if created:
                    bonuses_created += 1
                else:
                    if (bonus_obj.name or "") != (bonus_name or ""):
                        bonus_obj.name = bonus_name
                        bonus_obj.save(update_fields=["name"])
                        bonuses_updated += 1

                # Replace semantics for deterministic imports
                existing_qs = SetBonusRank.objects.filter(set_bonus=bonus_obj)
                deleted = existing_qs.count()
                if deleted:
                    existing_qs.delete()
                    ranks_deleted += deleted

                rank_map = merged.get(int(bonus_id), {})
                for mr in rank_map.values():
                    # We expect Skill(external_id) already exists from import_skills.
                    # If not, we create a minimal placeholder (so ranks are not lost).
                    skill_obj = skills_by_external.get(int(mr.skill_external_id))
                    if not skill_obj:
                        skill_obj = Skill.objects.create(
                            external_id=int(mr.skill_external_id),
                            name=f"Skill #{mr.skill_external_id}",
                            description="",
                            max_level=max(1, int(mr.level)),
                        )
                        skills_by_external[int(mr.skill_external_id)] = skill_obj
                        skill_placeholders_created += 1
                    else:
                        # Make sure max_level is at least the granted level
                        if int(skill_obj.max_level) < int(mr.level):
                            skill_obj.max_level = int(mr.level)
                            skill_obj.save(update_fields=["max_level"])

                    SetBonusRank.objects.create(
                        set_bonus=bonus_obj,
                        pieces=int(mr.pieces),
                        skill=skill_obj,
                        level=int(mr.level),
                        description=(mr.description or "").strip(),
                    )
                    ranks_created += 1
                    skills_linked_to_ranks += 1

        self._print_stats(
            scanned_sets=scanned_sets,
            distinct_bonuses=distinct_bonuses,
            merged_rank_total=merged_rank_total,
            bonuses_created=bonuses_created,
            bonuses_updated=bonuses_updated,
            ranks_created=ranks_created,
            ranks_deleted=ranks_deleted,
            skills_linked_to_ranks=skills_linked_to_ranks,
            skill_placeholders_created=skill_placeholders_created,
            skipped_bonus_none=skipped_bonus_none,
            skipped_bonus_invalid=skipped_bonus_invalid,
            skipped_bonus_no_ranks=skipped_bonus_no_ranks,
            skipped_rank_invalid=skipped_rank_invalid,
            dry_run=False,
        )

    def _print_stats(
        self,
        *,
        scanned_sets: int,
        distinct_bonuses: int,
        merged_rank_total: int,
        bonuses_created: int,
        bonuses_updated: int,
        ranks_created: int,
        ranks_deleted: int,
        skills_linked_to_ranks: int,
        skill_placeholders_created: int,
        skipped_bonus_none: int,
        skipped_bonus_invalid: int,
        skipped_bonus_no_ranks: int,
        skipped_rank_invalid: int,
        dry_run: bool,
    ) -> None:
        self.stdout.write(self.style.SUCCESS("Set bonus import completed."))
        self.stdout.write(f"Armor sets scanned: {scanned_sets}")
        self.stdout.write(f"Distinct SetBonus ids found: {distinct_bonuses}")
        self.stdout.write(f"Merged SetBonusRank rows (unique by pieces+skill+level): {merged_rank_total}")
        self.stdout.write(f"SetBonus created: {bonuses_created}")
        self.stdout.write(f"SetBonus updated: {bonuses_updated}")
        self.stdout.write(f"SetBonusRank created: {ranks_created}")
        self.stdout.write(f"SetBonusRank deleted (replace): {ranks_deleted}")
        self.stdout.write(f"Skills linked to ranks: {skills_linked_to_ranks}")
        self.stdout.write(f"Skill placeholders created: {skill_placeholders_created}")
        self.stdout.write(f"Skipped (bonus is None): {skipped_bonus_none}")
        self.stdout.write(f"Skipped (bonus invalid): {skipped_bonus_invalid}")
        self.stdout.write(f"Skipped (bonus has no ranks / int-only bonus): {skipped_bonus_no_ranks}")
        self.stdout.write(f"Skipped (invalid rank entries): {skipped_rank_invalid}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode enabled: no database changes were made."))