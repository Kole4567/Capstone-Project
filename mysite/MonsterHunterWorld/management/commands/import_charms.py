import json
from typing import Any, Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction

from MonsterHunterWorld.models import Charm, CharmSkill, Skill


# ==================================================
# JSON shape helpers (defensive)
# ==================================================
def extract_charm_list(payload: Any) -> List[dict]:
    """
    Return a list of charm dicts from various possible JSON shapes.

    Supported input shapes:
      1) [ {...}, {...}, ... ]  (plain array)
      2) { "charms": [ ... ] }
      3) { "data": { "charms": [ ... ] } }
      4) { "results": [ ... ] }
      5) { "data": [ ... ] }  (less common)
    """
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    candidates = [
        payload.get("charms"),
        (payload.get("data") or {}).get("charms") if isinstance(payload.get("data"), dict) else None,
        payload.get("results"),
        payload.get("data") if isinstance(payload.get("data"), list) else None,
    ]

    for c in candidates:
        if isinstance(c, list):
            return c

    return []


def safe_int(v: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        if v is None:
            return default
        return int(v)
    except (TypeError, ValueError):
        return default


def pick_external_id(obj: dict, keys: Tuple[str, ...] = ("external_id", "id")) -> Optional[int]:
    """
    Try multiple keys for external id.
    """
    if not isinstance(obj, dict):
        return None

    for k in keys:
        v = obj.get(k)
        if v is None:
            continue
        iv = safe_int(v, default=None)
        if iv is not None:
            return iv

    return None


def ensure_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, dict):
        return [x]
    return []


# ==================================================
# mhw-db charm parsers
# ==================================================
def extract_ranks(charm_dict: dict) -> List[dict]:
    """
    mhw-db charm usually:
      { id, name, ranks: [ { id, name, level, rarity, skills:[...] }, ... ] }
    """
    if not isinstance(charm_dict, dict):
        return []
    return [r for r in ensure_list(charm_dict.get("ranks")) if isinstance(r, dict)]


def derive_charm_rank_external_id(base_charm_id: int, rank_dict: dict) -> Optional[int]:
    """
    Prefer rank.id if provided (most stable).
    Fallback to a deterministic composite if rank.id is missing.
    """
    rank_id = pick_external_id(rank_dict, keys=("external_id", "id", "rankId"))
    if rank_id is not None:
        return rank_id

    level = safe_int(rank_dict.get("level"), default=None)
    if level is None:
        return None

    # Fallback composite (only used if rank has no id)
    # Assumption: level < 100 (true in MHW charms).
    return int(base_charm_id) * 100 + int(level)


def derive_charm_rank_name(base_name: str, rank_dict: dict) -> str:
    """
    Prefer rank.name (if present). Otherwise fallback to "Base Name Lv X".
    """
    rn = rank_dict.get("name")
    if rn is not None and str(rn).strip():
        return str(rn).strip()

    level = safe_int(rank_dict.get("level"), default=None)
    if level is not None:
        return f"{base_name} Lv {level}"

    return base_name


def extract_rank_skills(rank_dict: dict) -> List[Tuple[int, int]]:
    """
    mhw-db rank.skills is usually:
      skills: [ { "skill": <skillId>, "level": <int> }, ... ]

    But be defensive:
      - skill could be a dict: { "id": ... }
      - skills could be dict -> treat as list
    """
    out: List[Tuple[int, int]] = []

    skills_field = ensure_list(rank_dict.get("skills"))
    for entry in skills_field:
        if not isinstance(entry, dict):
            continue

        raw_skill = entry.get("skill")
        skill_level = safe_int(entry.get("level"), default=1) or 1
        skill_level = max(1, int(skill_level))

        skill_external_id: Optional[int] = None

        # Case A: skill is already an int id
        if isinstance(raw_skill, int) or isinstance(raw_skill, str):
            skill_external_id = safe_int(raw_skill, default=None)

        # Case B: skill is an object/dict { id, ... }
        elif isinstance(raw_skill, dict):
            skill_external_id = pick_external_id(raw_skill, keys=("external_id", "id", "skillId"))

        if skill_external_id is None:
            continue

        out.append((int(skill_external_id), int(skill_level)))

    return out


# ==================================================
# Command
# ==================================================
class Command(BaseCommand):
    help = "Import MHW charms data into the internal database (rank-based, mhw-db style)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--charms",
            type=str,
            required=True,
            help="Path to charms JSON file (e.g., data/mhw_charms_raw.json).",
        )

        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing charms (and their CharmSkill links) before importing.",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse only; do not write to DB.",
        )

        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of base charm records processed (0 = no limit).",
        )

    def handle(self, *args, **options):
        path = options["charms"]
        reset = options["reset"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        charms = extract_charm_list(payload)
        if not charms:
            self.stdout.write(self.style.ERROR("Invalid JSON: could not find a list of charms"))
            return

        if limit and limit > 0:
            charms = charms[:limit]

        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        charm_skills_created = 0
        charm_skills_deleted = 0
        skills_missing = 0

        # Preload Skill.external_id -> Skill.id for fast linking
        skill_id_by_external: Dict[int, int] = {
            int(s.external_id): int(s.id) for s in Skill.objects.all()
        }

        with transaction.atomic():
            if reset and not dry_run:
                CharmSkill.objects.all().delete()
                Charm.objects.all().delete()

            for idx, charm_dict in enumerate(charms, start=1):
                if not isinstance(charm_dict, dict):
                    skipped_count += 1
                    continue

                try:
                    base_id = pick_external_id(charm_dict, keys=("external_id", "id", "charmId"))
                    base_name = (charm_dict.get("name") or "").strip()

                    if base_id is None or not base_name:
                        skipped_count += 1
                        continue

                    ranks = extract_ranks(charm_dict)
                    if not ranks:
                        skipped_count += 1
                        continue

                    # Each rank becomes a Charm row in our DB (like your current design)
                    for rank in ranks:
                        rank_ext_id = derive_charm_rank_external_id(int(base_id), rank)
                        if rank_ext_id is None:
                            skipped_count += 1
                            continue

                        name = derive_charm_rank_name(base_name, rank)
                        rarity = safe_int(rank.get("rarity"), default=None)

                        if dry_run:
                            # Count as "would create" (approx)
                            created_count += 1
                            continue

                        obj, created = Charm.objects.get_or_create(
                            external_id=int(rank_ext_id),
                            defaults={
                                "name": name,
                                "rarity": rarity,
                            },
                        )

                        if created:
                            created_count += 1
                        else:
                            changed = False

                            if obj.name != name:
                                obj.name = name
                                changed = True

                            if obj.rarity != rarity:
                                obj.rarity = rarity
                                changed = True

                            if changed:
                                obj.save()
                                updated_count += 1

                        # Replace semantics for CharmSkill per charm rank
                        qs = CharmSkill.objects.filter(charm=obj)
                        deleted = qs.count()
                        if deleted:
                            qs.delete()
                            charm_skills_deleted += deleted

                        pairs = extract_rank_skills(rank)
                        for skill_external_id, lvl in pairs:
                            skill_id = skill_id_by_external.get(int(skill_external_id))
                            if not skill_id:
                                skills_missing += 1
                                continue

                            CharmSkill.objects.create(
                                charm=obj,
                                skill_id=int(skill_id),
                                level=max(1, int(lvl)),
                            )
                            charm_skills_created += 1

                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.WARNING(f"[{idx}] Failed charm import: {e}"))
                    continue

        self.stdout.write(self.style.SUCCESS("Charms import completed."))
        self.stdout.write(f"Charms created: {created_count}")
        self.stdout.write(f"Charms updated: {updated_count}")
        self.stdout.write(f"Charms skipped: {skipped_count}")
        self.stdout.write(f"Charms failed: {failed_count}")
        self.stdout.write(f"CharmSkill links created: {charm_skills_created}")
        self.stdout.write(f"CharmSkill links deleted: {charm_skills_deleted}")
        self.stdout.write(f"Skills missing (no Skill.external_id match): {skills_missing}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode: no DB changes were made."))