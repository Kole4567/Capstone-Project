import json

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from MonsterHunterWorld.models import Monster, MonsterWeakness, MonsterResistance


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
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    candidates = [
        payload.get("monsters"),
        (payload.get("data") or {}).get("monsters") if isinstance(payload.get("data"), dict) else None,
        payload.get("results"),
        payload.get("data") if isinstance(payload.get("data"), list) else None,
    ]

    for c in candidates:
        if isinstance(c, list):
            return c

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

    We scan a small prefix of the list to decide a best-guess format.
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

    Typical mhw-db shape:
      weaknesses: [
        { "element": "fire", "stars": 3, "condition": "..." },
        ...
      ]
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

        element = w.get("element") or w.get("name") or w.get("value")
        stars = w.get("stars") or w.get("level") or 0
        condition = w.get("condition") or w.get("when")

        if not element:
            continue

        try:
            stars_int = int(stars)
        except (ValueError, TypeError):
            stars_int = 0

        out.append(
            {
                "kind": "element",
                "name": str(element).title(),
                "stars": stars_int,
                "condition": condition,
            }
        )

    return out


def normalize_weaknesses_test(raw):
    """
    Normalize weaknesses for our custom/test style input.
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

        kind = pick_kind(w) or "unknown"
        name = w.get("name") or w.get("element") or w.get("value")
        stars = w.get("stars") or w.get("level") or 0
        condition = w.get("condition") or w.get("when")

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


# ==================================================
# Monster "Element" (offensive identity) normalizers
# ==================================================
def normalize_primary_element(elements_field):
    """
    Normalize monster "elements" into a single primary element.

    Observed shape (your data/mhw_monsters.json):
      "elements": ["fire", "water", ...]
    """
    if elements_field is None:
        return None

    if isinstance(elements_field, str):
        v = elements_field.strip().lower()
        return v if v else None

    if isinstance(elements_field, dict):
        elements_field = [elements_field]

    if not isinstance(elements_field, list) or not elements_field:
        return None

    first = elements_field[0]

    if isinstance(first, str):
        v = first.strip().lower()
        return v if v else None

    if isinstance(first, dict):
        v = first.get("type") or first.get("element") or first.get("name")
        if isinstance(v, str):
            v = v.strip().lower()
            return v if v else None

    return None


def normalize_primary_ailment(ailments_field):
    """
    Normalize monster "ailments" into a single primary ailment name.

    Observed shape (your data/mhw_monsters.json):
      "ailments": [{ "id": 8, "name": "Poison", ... }, ...]
    """
    if ailments_field is None:
        return None

    if isinstance(ailments_field, str):
        v = ailments_field.strip()
        return v if v else None

    if isinstance(ailments_field, dict):
        ailments_field = [ailments_field]

    if not isinstance(ailments_field, list) or not ailments_field:
        return None

    first = ailments_field[0]

    if isinstance(first, str):
        v = first.strip()
        return v if v else None

    if isinstance(first, dict):
        v = first.get("name") or first.get("type")
        if isinstance(v, str):
            v = v.strip()
            return v if v else None

    return None


# ==================================================
# Monster "Resistances" normalizers
# ==================================================
def normalize_resistances_mhwdb(raw):
    """
    Normalize mhw-db style resistances.

    Observed shape (your data/mhw_monsters.json):
      "resistances": [
        { "element": "water", "condition": None },
        { "element": "fire", "condition": "covered in mud" },
        ...
      ]

    Returns:
      [{ "element": "water", "condition": None }, ...]
    """
    if raw is None:
        return []

    if isinstance(raw, dict):
        raw = [raw]

    if not isinstance(raw, list):
        return []

    out = []
    for r in raw:
        if not isinstance(r, dict):
            continue

        element = r.get("element") or r.get("type") or r.get("name") or r.get("value")
        condition = r.get("condition") or r.get("when")

        if not element:
            continue

        el = str(element).strip().lower()
        if not el:
            continue

        if isinstance(condition, str):
            condition = condition.strip() or None

        out.append({"element": el, "condition": condition})

    return out


class Command(BaseCommand):
    help = "Import MHW monster data into the internal database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--monsters",
            type=str,
            required=True,
            help="Path to monsters JSON file",
        )

        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing monsters and weaknesses before importing",
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
            help="Limit number of monsters to import (0 = no limit)",
        )

    def handle(self, *args, **options):
        path = options["monsters"]
        reset = options["reset"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        # Load JSON from file
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        # Extract monster list from supported payload shapes
        monsters = extract_monster_list(payload)
        if not monsters:
            self.stdout.write(self.style.ERROR("Invalid JSON: could not find a list of monsters"))
            return

        # Apply optional limit for quick testing
        if limit and limit > 0:
            monsters = monsters[:limit]

        # Detect format (mhw-db vs test/custom) using heuristic
        is_mhw_db_format = detect_mhw_db_format(monsters)

        # Counters for summary output
        monsters_created = 0
        monsters_updated = 0
        monsters_skipped = 0
        monsters_failed = 0
        weaknesses_created = 0
        resistances_created = 0

        # Reset in its own atomic block for safety
        if reset and not dry_run:
            try:
                with transaction.atomic():
                    MonsterWeakness.objects.all().delete()
                    MonsterResistance.objects.all().delete()
                    Monster.objects.all().delete()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[RESET] Failed: {e}"))
                return

        # Import each monster in its own transaction (fail-safe)
        for idx, m in enumerate(monsters, start=1):
            if not isinstance(m, dict):
                monsters_skipped += 1
                continue

            safe_name = m.get("name") or "Unknown"

            try:
                with transaction.atomic():
                    external_id = pick_external_id(m)
                    name = m.get("name")

                    # Monster "offensive identity" fields (independent of weakness format)
                    primary_element = normalize_primary_element(m.get("elements"))
                    primary_ailment = normalize_primary_ailment(m.get("ailments"))

                    # Resistances (mhw-db JSON has it regardless of weakness format)
                    resistances_norm = normalize_resistances_mhwdb(m.get("resistances"))

                    # Format-specific mapping
                    if is_mhw_db_format:
                        monster_type = m.get("species") or m.get("monster_type") or ""
                        is_elder_dragon = str(monster_type).lower() == "elder dragon"
                        weaknesses_norm = normalize_weaknesses_mhwdb(m.get("weaknesses"))
                    else:
                        monster_type = m.get("monster_type", "") or m.get("species") or ""
                        is_elder_dragon = bool(m.get("is_elder_dragon", False))
                        weaknesses_norm = normalize_weaknesses_test(m.get("weaknesses"))

                    # Required fields check
                    if external_id is None or not name:
                        monsters_skipped += 1
                        continue

                    # Dry-run: count only, no DB writes
                    if dry_run:
                        monsters_created += 1
                        weaknesses_created += len(weaknesses_norm)
                        resistances_created += len(resistances_norm)
                        continue

                    # Upsert monster record
                    monster_obj, created = Monster.objects.update_or_create(
                        external_id=int(external_id),
                        defaults={
                            "name": name,
                            "monster_type": monster_type,
                            "is_elder_dragon": bool(is_elder_dragon),
                            "primary_element": primary_element,
                            "primary_ailment": primary_ailment,
                        },
                    )

                    if created:
                        monsters_created += 1
                    else:
                        monsters_updated += 1

                    # Replace weaknesses (keeps DB in sync with JSON)
                    MonsterWeakness.objects.filter(monster=monster_obj).delete()

                    # Dedupe weaknesses using the same key as the DB unique constraint:
                    # (monster, kind, name, condition_key)
                    # Keep the highest stars value when duplicates exist.
                    seen_weakness: dict[tuple[str, str, str], tuple[int, str | None]] = {}

                    for w in weaknesses_norm:
                        kind = w.get("kind") or "unknown"
                        w_name = w.get("name")
                        cond = w.get("condition")

                        if isinstance(cond, str):
                            cond = cond.strip() or None

                        if not w_name:
                            continue

                        stars_raw = w.get("stars") or 0
                        try:
                            stars = int(stars_raw)
                        except (ValueError, TypeError):
                            stars = 0

                        if stars <= 0:
                            continue

                        condition_key = slugify(cond) if cond else ""
                        key = (str(kind), str(w_name), str(condition_key))

                        if key not in seen_weakness or stars > seen_weakness[key][0]:
                            seen_weakness[key] = (stars, cond)

                    for (kind, w_name, condition_key), (stars, cond) in seen_weakness.items():
                        MonsterWeakness.objects.create(
                            monster=monster_obj,
                            kind=kind,
                            name=w_name,
                            stars=stars,
                            condition=cond,
                            condition_key=condition_key,
                        )
                        weaknesses_created += 1

                    # Replace resistances (keeps DB in sync with JSON)
                    MonsterResistance.objects.filter(monster=monster_obj).delete()

                    # Dedupe resistances by (element, condition_key)
                    seen_res = set()
                    for r in resistances_norm:
                        element = r.get("element")
                        cond = r.get("condition")

                        if not element:
                            continue

                        if isinstance(cond, str):
                            cond = cond.strip() or None

                        condition_key = slugify(cond) if cond else ""
                        key = (str(element), str(condition_key))
                        if key in seen_res:
                            continue
                        seen_res.add(key)

                        MonsterResistance.objects.create(
                            monster=monster_obj,
                            element=str(element),
                            condition=cond,
                            condition_key=condition_key,
                        )
                        resistances_created += 1

            except Exception as e:
                monsters_failed += 1
                self.stdout.write(self.style.ERROR(f"[{idx}] {safe_name} import failed: {e}"))
                continue

        # Final summary output
        self.stdout.write(self.style.SUCCESS("Import completed."))
        self.stdout.write(f"Format detected: {'mhw-db' if is_mhw_db_format else 'test/custom'}")
        self.stdout.write(f"Monsters created: {monsters_created}")
        self.stdout.write(f"Monsters updated: {monsters_updated}")
        self.stdout.write(f"Monsters skipped: {monsters_skipped}")
        self.stdout.write(f"Monsters failed: {monsters_failed}")
        self.stdout.write(f"Weaknesses created: {weaknesses_created}")
        self.stdout.write(f"Resistances created: {resistances_created}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode: no DB changes were made."))