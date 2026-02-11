import json

from django.core.management.base import BaseCommand
from django.db import transaction

from MonsterHunterWorld.models import Decoration, DecorationSkill, Skill


# ==================================================
# Defensive JSON helpers
# ==================================================
def extract_decoration_list(payload):
    """
    Return a list of decoration dicts from various possible JSON shapes.

    Supported input shapes:
      1) [ {...}, {...}, ... ]
      2) { "decorations": [ ... ] }
      3) { "data": { "decorations": [ ... ] } }
      4) { "results": [ ... ] }
      5) { "data": [ ... ] }
    """
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    candidates = [
        payload.get("decorations"),
        (payload.get("data") or {}).get("decorations")
        if isinstance(payload.get("data"), dict)
        else None,
        payload.get("results"),
        payload.get("data") if isinstance(payload.get("data"), list) else None,
    ]

    for c in candidates:
        if isinstance(c, list):
            return c

    return []


def safe_int(v, default=None):
    try:
        if v is None:
            return default
        return int(v)
    except (TypeError, ValueError):
        return default


def pick_external_id(obj: dict):
    """
    Try multiple keys for external id.
    Common candidates in mhw-db: id
    Sometimes: external_id
    """
    if not isinstance(obj, dict):
        return None

    for k in ("external_id", "id"):
        v = obj.get(k)
        out = safe_int(v, None)
        if out is not None:
            return out
    return None


def extract_decoration_skills(decoration_dict: dict):
    """
    mhw-db typical shape:
      skills: [
        { "skill": { "id": 1, ... }, "level": 1 },
        ...
      ]

    Also tolerate:
      { "skill": 1, "level": 1 }
      { "skillId": 1, "level": 1 }
      or even list of ints
    """
    if not isinstance(decoration_dict, dict):
        return []

    skills_field = decoration_dict.get("skills") or []
    if isinstance(skills_field, dict):
        skills_field = [skills_field]
    if not isinstance(skills_field, list):
        return []

    out = []
    for entry in skills_field:
        # entry can be int, dict, etc.
        if isinstance(entry, int):
            out.append((entry, 1))
            continue

        if not isinstance(entry, dict):
            continue

        level = safe_int(entry.get("level"), 1) or 1

        # skill can be dict or int
        s = entry.get("skill")
        if isinstance(s, dict):
            skill_external_id = safe_int(s.get("id") or s.get("external_id"), None)
        else:
            skill_external_id = safe_int(s, None)

        # fallback keys some datasets use
        if skill_external_id is None:
            skill_external_id = safe_int(entry.get("skillId") or entry.get("skill_id"), None)

        if skill_external_id is None:
            continue

        out.append((skill_external_id, max(1, level)))

    return out


# ==================================================
# Command
# ==================================================
class Command(BaseCommand):
    help = "Import MHW decorations data into the internal database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--decorations",
            type=str,
            required=True,
            help="Path to decorations JSON file",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing decorations (and DecorationSkill links) before importing",
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
            help="Limit number of decorations to import (0 = no limit)",
        )

    def handle(self, *args, **options):
        path = options["decorations"]
        reset = options["reset"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        decorations = extract_decoration_list(payload)
        if not decorations:
            self.stdout.write(self.style.ERROR("Invalid JSON: could not find a list of decorations"))
            return

        if limit and limit > 0:
            decorations = decorations[:limit]

        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        links_created = 0
        links_deleted = 0
        skills_missing = 0

        with transaction.atomic():
            if reset and not dry_run:
                DecorationSkill.objects.all().delete()
                Decoration.objects.all().delete()

            for idx, d in enumerate(decorations, start=1):
                if not isinstance(d, dict):
                    skipped_count += 1
                    continue

                try:
                    external_id = pick_external_id(d)
                    name = (d.get("name") or "").strip()
                    rarity = safe_int(d.get("rarity"), 1) or 1

                    if external_id is None or not name:
                        skipped_count += 1
                        continue

                    if dry_run:
                        created_count += 1
                        continue

                    obj, created = Decoration.objects.get_or_create(
                        external_id=int(external_id),
                        defaults={"name": name, "rarity": int(rarity)},
                    )

                    if created:
                        created_count += 1
                    else:
                        changed = False
                        if obj.name != name:
                            obj.name = name
                            changed = True
                        if int(obj.rarity) != int(rarity):
                            obj.rarity = int(rarity)
                            changed = True
                        if changed:
                            obj.save()
                            updated_count += 1

                    # Replace semantics for join rows (per decoration)
                    existing = DecorationSkill.objects.filter(decoration=obj)
                    deleted = existing.count()
                    if deleted:
                        existing.delete()
                        links_deleted += deleted

                    pairs = extract_decoration_skills(d)
                    if not pairs:
                        continue

                    for skill_external_id, level in pairs:
                        # IMPORTANT: decoration payload uses mhw-db skill id -> our Skill.external_id
                        skill_obj = Skill.objects.filter(external_id=int(skill_external_id)).first()
                        if not skill_obj:
                            skills_missing += 1
                            continue

                        DecorationSkill.objects.create(
                            decoration=obj,
                            skill=skill_obj,
                            level=max(1, int(level)),
                        )
                        links_created += 1

                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.WARNING(f"[{idx}] Failed decoration import: {e}"))
                    continue

        self.stdout.write(self.style.SUCCESS("Decorations import completed."))
        self.stdout.write(f"Decorations created: {created_count}")
        self.stdout.write(f"Decorations updated: {updated_count}")
        self.stdout.write(f"Decorations skipped: {skipped_count}")
        self.stdout.write(f"Decorations failed: {failed_count}")
        self.stdout.write(f"DecorationSkill links created: {links_created}")
        self.stdout.write(f"DecorationSkill links deleted: {links_deleted}")
        self.stdout.write(f"Skills missing (no Skill.external_id match): {skills_missing}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode: no DB changes were made."))