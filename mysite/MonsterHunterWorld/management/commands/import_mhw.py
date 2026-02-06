import json

from django.core.management.base import BaseCommand
from django.db import transaction

from MonsterHunterWorld.models import Monster, MonsterWeakness


def extract_monster_list(payload):
    """
    Return a list of monster dicts from various possible JSON shapes.

    Supported input shapes:
      1) [ {...}, {...}, ... ]  (plain array)
      2) { "monsters": [ ... ] }
      3) { "data": { "monsters": [ ... ] } }
      4) { "results": [ ... ] }
      5) { "data": [ ... ] }  (less common, but sometimes used)
    """
    # Case 1: already a list
    if isinstance(payload, list):
        return payload

    # If it's not a dict or list, we cannot parse it safely
    if not isinstance(payload, dict):
        return []

    # Try common wrapper fields in a safe way (never KeyError)
    candidates = [
        payload.get("monsters"),
        (payload.get("data") or {}).get("monsters") if isinstance(payload.get("data"), dict) else None,
        payload.get("results"),
        payload.get("data") if isinstance(payload.get("data"), list) else None,
    ]

    # Return the first candidate that is actually a list
    for c in candidates:
        if isinstance(c, list):
            return c

    # If nothing matched, return empty list (caller will treat as invalid)
    return []


def pick_external_id(monster_dict: dict):
    """
    Try multiple keys for external id because different sources might use different field names.
    Returns an int if possible, otherwise None.

    Common candidates:
      - external_id
      - id
      - gameId
      - monsterId
    """
    if not isinstance(monster_dict, dict):
        return None

    for k in ("external_id", "id", "gameId", "monsterId"):
        v = monster_dict.get(k)
        if v is None:
            continue

        # Make a best effort to convert to int. If it fails, treat as missing.
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    return None


def detect_mhw_db_format(monsters: list) -> bool:
    """
    Heuristic detection:
    - mhw-db format weaknesses usually contain 'element' keys like:
        weaknesses: [{ "element": "fire", "stars": 3, "condition": "..." }, ...]
    - Our custom/test format uses:
        weaknesses: [{ "kind": "...", "name": "...", ... }, ...]

    We scan a small prefix of the list to decide a "best guess" format.
    """
    for item in monsters[:10]:
        if not isinstance(item, dict):
            continue

        w = item.get("weaknesses")
        if isinstance(w, list) and w:
            first = w[0]
            if isinstance(first, dict) and ("element" in first or "stars" in first):
                return True

    return False


def pick_kind(w: dict) -> str | None:
    """
    Weakness 'kind' might be stored under different keys depending on the source.
    This function tries multiple keys in priority order.
    """
    if not isinstance(w, dict):
        return None

    return (
        w.get("kind")
        or w.get("type")
        or w.get("element")
        or w.get("category")
    )


def normalize_weaknesses_mhwdb(raw):
    """
    Normalize weaknesses for mhw-db style input.

    Expected mhw-db shape (typical):
      weaknesses: [
        { "element": "fire", "stars": 3, "condition": "..." },
        ...
      ]

    But we also tolerate:
      - weaknesses as a dict (single item) -> wrap into list
      - missing keys -> use defaults and/or skip invalid items
      - weird types -> ignore safely
    """
    # If it's missing, treat as no weaknesses
    if raw is None:
        return []

    # If it's a single object, make it a list of one
    if isinstance(raw, dict):
        raw = [raw]

    # If it's not list/dict, we can't parse it
    if not isinstance(raw, list):
        return []

    out = []

    for w in raw:
        # Skip non-dict entries to avoid KeyError / attribute errors
        if not isinstance(w, dict):
            continue

        # mhw-db uses 'element', but we also accept fallback keys
        element = w.get("element") or w.get("name") or w.get("value")

        # stars might appear as 'stars' or 'level', or be missing
        stars = w.get("stars") or w.get("level") or 0

        # condition might appear under different names
        condition = w.get("condition") or w.get("when")

        # If we don't have an element name, the weakness entry is not usable
        if not element:
            continue

        # Ensure stars is an int; if conversion fails, default to 0
        try:
            stars_int = int(stars)
        except (ValueError, TypeError):
            stars_int = 0

        # Output is normalized to our internal schema
        out.append(
            {
                "kind": "element",
                "name": str(element).title(),  # "fire" -> "Fire"
                "stars": stars_int,
                "condition": condition,
            }
        )

    return out


def normalize_weaknesses_test(raw):
    """
    Normalize weaknesses for our custom/test style input.

    Expected test/custom shape:
      weaknesses: [
        { "kind": "element", "name": "Fire", "stars": 3, "condition": null },
        ...
      ]

    But we also tolerate:
      - weaknesses as a dict -> wrap into list
      - missing kind -> try fallback keys or use "unknown"
      - missing name -> try fallback keys
      - weird types -> skip safely
    """
    if raw is None:
        return []

    if isinstance(raw, dict):
        raw = [raw]

    if not isinstance(raw, list):
        return []

    out = []

    for w in raw:
        if not isinstance(w, dict):
            continue

        # Kind can be missing; try alternatives, then fallback to "unknown"
        kind = pick_kind(w) or "unknown"

        # Name might be 'name', or a source might store it under element/value
        name = w.get("name") or w.get("element") or w.get("value")

        # Stars can also be called level; default to 0 if missing
        stars = w.get("stars") or w.get("level") or 0

        # Condition might be stored as 'condition' or 'when'
        condition = w.get("condition") or w.get("when")

        # If both kind is unknown AND name is missing, this entry has no meaning
        if (not kind or kind == "unknown") and not name:
            continue

        try:
            stars_int = int(stars)
        except (ValueError, TypeError):
            stars_int = 0

        out.append(
            {
                "kind": str(kind),
                "name": str(name) if name is not None else None,
                "stars": stars_int,
                "condition": condition,
            }
        )

    return out


class Command(BaseCommand):
    help = "Import MHW monster data into the internal database."

    def add_arguments(self, parser):
        # Path to the JSON file (required)
        parser.add_argument(
            "--monsters",
            type=str,
            required=True,
            help="Path to monsters JSON file",
        )

        # Reset flag: delete existing data first (safe order, inside a transaction)
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing monsters and weaknesses before importing",
        )

        # Dry-run: parse input and count what would happen, but do not write to DB
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse only; do not write to DB",
        )

        # Limit: import only first N monsters for quick testing
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of monsters to import (0 = no limit)",
        )

    def handle(self, *args, **options):
        path = options["monsters"]
        reset = options["reset"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        # 1) Load JSON from file
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        # 2) Extract monster list from supported payload shapes
        monsters = extract_monster_list(payload)
        if not monsters:
            self.stdout.write(self.style.ERROR("Invalid JSON: could not find a list of monsters"))
            return

        # 3) Apply optional limit for quick testing
        if limit and limit > 0:
            monsters = monsters[:limit]

        # 4) Detect format (mhw-db vs test/custom) using heuristic
        is_mhw_db_format = detect_mhw_db_format(monsters)

        # Counters for summary output
        monsters_created = 0
        monsters_updated = 0
        monsters_skipped = 0
        monsters_failed = 0
        weaknesses_created = 0

        # 5) Wrap reset + import in a single transaction.
        #    This prevents "half-deleted / half-imported" states if something fails.
        with transaction.atomic():
            # 5a) Handle reset safely (child tables first, then parent tables)
            if reset and not dry_run:
                MonsterWeakness.objects.all().delete()
                Monster.objects.all().delete()

            # 5b) Import each monster record independently.
            #     We still guard each record with try/except so one bad record won't kill the whole import.
            for idx, m in enumerate(monsters, start=1):
                # Skip non-dict entries
                if not isinstance(m, dict):
                    monsters_skipped += 1
                    continue

                try:
                    # External ID: required for stable upsert-like behavior
                    external_id = pick_external_id(m)

                    # Name: required field (if missing, skip)
                    name = m.get("name")

                    # Format-specific mapping
                    if is_mhw_db_format:
                        # mhw-db commonly uses 'species' as a type name
                        monster_type = m.get("species") or m.get("monster_type") or ""

                        # Elder dragon detection based on species string
                        is_elder_dragon = str(monster_type).lower() == "elder dragon"

                        # Normalize mhw-db weaknesses into our internal schema
                        weaknesses_norm = normalize_weaknesses_mhwdb(m.get("weaknesses"))
                    else:
                        # test/custom uses 'monster_type' and an explicit is_elder_dragon boolean
                        monster_type = m.get("monster_type", "") or m.get("species") or ""
                        is_elder_dragon = bool(m.get("is_elder_dragon", False))

                        # Normalize test/custom weaknesses into our internal schema
                        weaknesses_norm = normalize_weaknesses_test(m.get("weaknesses"))

                    # If required fields are missing, skip the record
                    if external_id is None or not name:
                        monsters_skipped += 1
                        continue

                    # Dry-run: count only, no DB writes
                    if dry_run:
                        monsters_created += 1
                        weaknesses_created += len(weaknesses_norm)
                        continue

                    # 6) "Upsert-like" behavior:
                    #    - If external_id exists -> get it
                    #    - If not -> create new monster
                    monster_obj, created = Monster.objects.get_or_create(
                        external_id=int(external_id),
                        defaults={
                            "name": name,
                            "monster_type": monster_type,
                            "is_elder_dragon": bool(is_elder_dragon),
                        },
                    )

                    if created:
                        monsters_created += 1
                    else:
                        # Keep DB in sync by updating if fields changed
                        changed = False
                        if monster_obj.name != name:
                            monster_obj.name = name
                            changed = True
                        if monster_obj.monster_type != monster_type:
                            monster_obj.monster_type = monster_type
                            changed = True
                        if monster_obj.is_elder_dragon != bool(is_elder_dragon):
                            monster_obj.is_elder_dragon = bool(is_elder_dragon)
                            changed = True

                        if changed:
                            monster_obj.save()
                            monsters_updated += 1

                    # 7) Weaknesses strategy (safe + simple):
                    #    Always "replace" weaknesses for the monster on each import.
                    MonsterWeakness.objects.filter(monster=monster_obj).delete()

                    # Insert normalized weaknesses (skip any entry missing a name)
                    for w in weaknesses_norm:
                        if not w.get("name"):
                            continue

                        # IMPORTANT:
                        # We treat stars <= 0 as invalid/unknown data and skip it.
                        # The API contract expects stars to be in the 1–3 range.
                        stars_raw = w.get("stars") or 0
                        try:
                            stars_int = int(stars_raw)
                        except (ValueError, TypeError):
                            stars_int = 0

                        if stars_int <= 0:
                            continue

                        MonsterWeakness.objects.create(
                            monster=monster_obj,
                            # Provide a safe fallback for kind to avoid NOT NULL issues
                            kind=w.get("kind") or "unknown",
                            name=w.get("name"),
                            stars=stars_int,
                            condition=w.get("condition"),
                        )
                        weaknesses_created += 1

                except Exception as e:
                    # Log the error but keep going for the next monster
                    monsters_failed += 1
                    self.stdout.write(self.style.WARNING(f"[{idx}] Failed monster import: {e}"))
                    continue

        # 8) Final summary output
        self.stdout.write(self.style.SUCCESS("Import completed."))
        self.stdout.write(f"Format detected: {'mhw-db' if is_mhw_db_format else 'test/custom'}")
        self.stdout.write(f"Monsters created: {monsters_created}")
        self.stdout.write(f"Monsters updated: {monsters_updated}")
        self.stdout.write(f"Monsters skipped: {monsters_skipped}")
        self.stdout.write(f"Monsters failed: {monsters_failed}")
        self.stdout.write(f"Weaknesses created: {weaknesses_created}")

        # Make dry-run status explicit
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode: no DB changes were made."))