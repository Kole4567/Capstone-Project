import json

from django.core.management.base import BaseCommand
from django.db import transaction

from MonsterHunterWorld.models import Skill


# ==================================================
# JSON shape helpers (defensive)
# ==================================================
def extract_skill_list(payload):
    """
    Return a list of skill dicts from various possible JSON shapes.

    Supported input shapes:
      1) [ {...}, {...}, ... ]  (plain array)
      2) { "skills": [ ... ] }
      3) { "data": { "skills": [ ... ] } }
      4) { "results": [ ... ] }
      5) { "data": [ ... ] }  (less common)
    """
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    data = payload.get("data")

    candidates = [
        payload.get("skills"),
        (data or {}).get("skills") if isinstance(data, dict) else None,
        payload.get("results"),
        data if isinstance(data, list) else None,
    ]

    for c in candidates:
        if isinstance(c, list):
            return c

    return []


def pick_external_id(skill_dict: dict):
    """
    Try multiple keys for external id.
    Common candidates: external_id, id, skillId
    """
    if not isinstance(skill_dict, dict):
        return None

    for k in ("external_id", "id", "skillId"):
        v = skill_dict.get(k)
        if v is None:
            continue
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    return None


def safe_int(v, default=0):
    try:
        if v is None:
            return default
        return int(v)
    except (ValueError, TypeError):
        return default


def derive_max_level(ranks_field):
    """
    mhw-db usually provides:
      ranks: [{ "level": 1, ... }, { "level": 2, ... }, ...]

    Policy (MHW-like, robust):
    - If ranks include "level", max_level = max(level)
    - Else if ranks is a list, max_level = len(ranks)
    - Else max_level = 1
    """
    if ranks_field is None:
        return 1

    if isinstance(ranks_field, dict):
        ranks_field = [ranks_field]

    if not isinstance(ranks_field, list) or not ranks_field:
        return 1

    levels = []
    for r in ranks_field:
        if not isinstance(r, dict):
            continue
        if "level" in r:
            lvl = safe_int(r.get("level"), default=None)
            if lvl is not None and lvl > 0:
                levels.append(lvl)

    if levels:
        return max(levels)

    return max(1, len(ranks_field))


# ==================================================
# Command
# ==================================================
class Command(BaseCommand):
    help = "Import MHW skill data into the internal database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skills",
            type=str,
            required=True,
            help="Path to skills JSON file",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing skills before importing",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse only; do not write to DB",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of skills to import (0 = no limit)",
        )

    def handle(self, *args, **options):
        path = options["skills"]
        reset = options["reset"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        skills = extract_skill_list(payload)
        if not skills:
            self.stdout.write(self.style.ERROR("Invalid JSON: could not find a list of skills"))
            return

        if limit and limit > 0:
            skills = skills[:limit]

        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        # NOTE (MHW-like import contract):
        # - Skill is the "source of truth" for:
        #   name / description / max_level
        # - Other importers (armors/decorations/charms/set_bonuses) should only "link"
        #   and never overwrite these fields aggressively.
        #
        # Here we DO overwrite when source changed, because this file is the owner.

        with transaction.atomic():
            if reset and not dry_run:
                Skill.objects.all().delete()

            for idx, s in enumerate(skills, start=1):
                if not isinstance(s, dict):
                    skipped_count += 1
                    continue

                try:
                    external_id = pick_external_id(s)

                    name = (s.get("name") or "").strip()
                    description = s.get("description") or ""
                    max_level = derive_max_level(s.get("ranks"))

                    if external_id is None or not name:
                        skipped_count += 1
                        continue

                    if dry_run:
                        created_count += 1
                        continue

                    obj, created = Skill.objects.get_or_create(
                        external_id=int(external_id),
                        defaults={
                            "name": name,
                            "description": description,
                            "max_level": int(max_level),
                        },
                    )

                    if created:
                        created_count += 1
                        continue

                    changed = False

                    if obj.name != name:
                        obj.name = name
                        changed = True

                    # Keep description in sync (mhw-db descriptions can be updated/cleaned)
                    if (obj.description or "") != (description or ""):
                        obj.description = description
                        changed = True

                    # Always sync max_level to the authoritative value from skill ranks
                    new_max = int(max_level)
                    if int(obj.max_level) != new_max:
                        obj.max_level = new_max
                        changed = True

                    if changed:
                        obj.save()
                        updated_count += 1

                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.WARNING(f"[{idx}] Failed skill import: {e}"))
                    continue

        self.stdout.write(self.style.SUCCESS("Skill import completed."))
        self.stdout.write(f"Skills created: {created_count}")
        self.stdout.write(f"Skills updated: {updated_count}")
        self.stdout.write(f"Skills skipped: {skipped_count}")
        self.stdout.write(f"Skills failed: {failed_count}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode: no DB changes were made."))