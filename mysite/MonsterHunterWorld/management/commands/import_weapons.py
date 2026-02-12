import json

from django.core.management.base import BaseCommand
from django.db import transaction

from MonsterHunterWorld.models import Weapon


def extract_weapon_list(payload):
    """
    Return a list of weapon dicts from various possible JSON shapes.

    Supported input shapes:
      1) [ {...}, {...}, ... ]  (plain array)
      2) { "weapons": [ ... ] }
      3) { "data": { "weapons": [ ... ] } }
      4) { "results": [ ... ] }
      5) { "data": [ ... ] }  (less common, but sometimes used)
    """
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    candidates = [
        payload.get("weapons"),
        (payload.get("data") or {}).get("weapons")
        if isinstance(payload.get("data"), dict)
        else None,
        payload.get("results"),
        payload.get("data") if isinstance(payload.get("data"), list) else None,
    ]

    for c in candidates:
        if isinstance(c, list):
            return c

    return []


def pick_external_id(weapon_dict: dict):
    """
    Try multiple keys for external id because different sources might use different field names.
    Returns an int if possible, otherwise None.

    Common candidates:
      - external_id
      - id
      - weaponId
    """
    if not isinstance(weapon_dict, dict):
        return None

    for k in ("external_id", "id", "weaponId"):
        v = weapon_dict.get(k)
        if v is None:
            continue
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    return None


def normalize_element(elements_field):
    """
    Normalize mhw-db 'elements' into a single (element, element_damage) pair.

    mhw-db typical:
      "elements": [
        { "type": "fire", "damage": 240, "hidden": false },
        ...
      ]

    MVP policy:
    - Take the first element entry if present.
    - Convert type -> Title case (Fire, Water, etc.)
    - Keep damage as int
    - If missing/invalid -> return (None, None)
    """
    if elements_field is None:
        return None, None

    if isinstance(elements_field, dict):
        elements_field = [elements_field]

    if not isinstance(elements_field, list) or not elements_field:
        return None, None

    first = elements_field[0]
    if not isinstance(first, dict):
        return None, None

    etype = first.get("type") or first.get("element") or first.get("name")
    dmg = first.get("damage") or first.get("value")

    if not etype:
        return None, None

    try:
        dmg_int = int(dmg) if dmg is not None else None
    except (ValueError, TypeError):
        dmg_int = None

    return str(etype).title(), dmg_int


def normalize_attack(attack_field):
    """
    Normalize mhw-db 'attack' object.

    mhw-db typical:
      "attack": { "display": 384, "raw": 120 }

    We store both display and raw when possible.
    """
    if not isinstance(attack_field, dict):
        return 0, 0

    display = attack_field.get("display", 0)
    raw = attack_field.get("raw", 0)

    try:
        display_int = int(display)
    except (ValueError, TypeError):
        display_int = 0

    try:
        raw_int = int(raw)
    except (ValueError, TypeError):
        raw_int = 0

    return display_int, raw_int


def normalize_affinity(weapon_dict: dict):
    """
    Normalize affinity.

    Note:
    - In mhw_weapons.json, affinity is commonly stored under weapon["attributes"]["affinity"].
    - Some sources may also provide a top-level "affinity".
    """
    if not isinstance(weapon_dict, dict):
        return 0

    # Prefer attributes.affinity (mhw-db style)
    attrs = weapon_dict.get("attributes")
    if isinstance(attrs, dict) and "affinity" in attrs:
        val = attrs.get("affinity", 0)
    else:
        # Fallback to top-level affinity if present
        val = weapon_dict.get("affinity", 0)

    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


class Command(BaseCommand):
    help = "Import MHW weapon data into the internal database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--weapons",
            type=str,
            required=True,
            help="Path to weapons JSON file",
        )

        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing weapons before importing",
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
            help="Limit number of weapons to import (0 = no limit)",
        )

    def handle(self, *args, **options):
        path = options["weapons"]
        reset = options["reset"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        # 1) Load JSON from file
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        # 2) Extract list
        weapons = extract_weapon_list(payload)
        if not weapons:
            self.stdout.write(self.style.ERROR("Invalid JSON: could not find a list of weapons"))
            return

        if limit and limit > 0:
            weapons = weapons[:limit]

        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        with transaction.atomic():
            if reset and not dry_run:
                Weapon.objects.all().delete()

            for idx, w in enumerate(weapons, start=1):
                if not isinstance(w, dict):
                    skipped_count += 1
                    continue

                try:
                    external_id = pick_external_id(w)
                    name = w.get("name")
                    weapon_type = w.get("type") or w.get("weapon_type")
                    rarity = w.get("rarity")

                    # Required fields check
                    if external_id is None or not name or not weapon_type or rarity is None:
                        skipped_count += 1
                        continue

                    # Normalize nested fields
                    attack_display, attack_raw = normalize_attack(w.get("attack"))
                    element, element_damage = normalize_element(w.get("elements"))

                    # IMPORTANT: affinity is typically stored under attributes.affinity (mhw-db)
                    affinity_int = normalize_affinity(w)

                    elderseal = w.get("elderseal")

                    # Dry-run: count only
                    if dry_run:
                        created_count += 1
                        continue

                    weapon_obj, created = Weapon.objects.get_or_create(
                        external_id=int(external_id),
                        defaults={
                            "name": name,
                            "weapon_type": weapon_type,
                            "rarity": int(rarity),
                            "attack_display": attack_display,
                            "attack_raw": attack_raw,
                            "element": element,
                            "element_damage": element_damage,
                            "affinity": affinity_int,
                            "elderseal": elderseal,
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        changed = False

                        if weapon_obj.name != name:
                            weapon_obj.name = name
                            changed = True

                        if weapon_obj.weapon_type != weapon_type:
                            weapon_obj.weapon_type = weapon_type
                            changed = True

                        if weapon_obj.rarity != int(rarity):
                            weapon_obj.rarity = int(rarity)
                            changed = True

                        if weapon_obj.attack_display != attack_display:
                            weapon_obj.attack_display = attack_display
                            changed = True

                        if weapon_obj.attack_raw != attack_raw:
                            weapon_obj.attack_raw = attack_raw
                            changed = True

                        if weapon_obj.element != element:
                            weapon_obj.element = element
                            changed = True

                        if weapon_obj.element_damage != element_damage:
                            weapon_obj.element_damage = element_damage
                            changed = True

                        if weapon_obj.affinity != affinity_int:
                            weapon_obj.affinity = affinity_int
                            changed = True

                        if weapon_obj.elderseal != elderseal:
                            weapon_obj.elderseal = elderseal
                            changed = True

                        if changed:
                            weapon_obj.save()
                            updated_count += 1

                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.WARNING(f"[{idx}] Failed weapon import: {e}"))
                    continue

        self.stdout.write(self.style.SUCCESS("Weapon import completed."))
        self.stdout.write(f"Weapons created: {created_count}")
        self.stdout.write(f"Weapons updated: {updated_count}")
        self.stdout.write(f"Weapons skipped: {skipped_count}")
        self.stdout.write(f"Weapons failed: {failed_count}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode: no DB changes were made."))