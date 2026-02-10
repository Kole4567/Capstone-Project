import json

from django.core.management.base import BaseCommand
from django.db import transaction

from MonsterHunterWorld.models import Armor, ArmorSkill, Skill


# ==================================================
# JSON shape helpers (defensive)
# ==================================================
def extract_armor_list(payload):
    """
    Return a list of armor dicts from various possible JSON shapes.

    Supported input shapes:
      1) [ {...}, {...}, ... ]  (plain array)
      2) { "armor": [ ... ] }
      3) { "armors": [ ... ] }
      4) { "data": { "armors": [ ... ] } }
      5) { "results": [ ... ] }
      6) { "data": [ ... ] }  (less common)
    """
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    candidates = [
        payload.get("armors"),
        payload.get("armor"),
        (payload.get("data") or {}).get("armors") if isinstance(payload.get("data"), dict) else None,
        payload.get("results"),
        payload.get("data") if isinstance(payload.get("data"), list) else None,
    ]

    for c in candidates:
        if isinstance(c, list):
            return c

    return []


def pick_external_id(obj: dict):
    """
    Try multiple keys for external id.
    Common candidates: external_id, id
    """
    if not isinstance(obj, dict):
        return None

    for k in ("external_id", "id"):
        v = obj.get(k)
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


def normalize_armor_type(raw):
    """
    mhw-db armor type is usually: head, chest, gloves, waist, legs.
    Keep as-is, but normalize common variants defensively.
    """
    if not raw:
        return ""
    t = str(raw).strip().lower()

    aliases = {
        "helm": "head",
        "helmet": "head",
        "head": "head",
        "chest": "chest",
        "mail": "chest",
        "arms": "gloves",
        "gloves": "gloves",
        "gauntlets": "gloves",
        "waist": "waist",
        "coil": "waist",
        "legs": "legs",
        "greaves": "legs",
    }
    return aliases.get(t, t)


def extract_defense(defense_field):
    """
    mhw-db usually provides:
      defense: { "base": 64, "max": 84, "augmented": 94 }

    Returns (base, max, augmented) as ints.
    """
    if not isinstance(defense_field, dict):
        return 0, 0, 0

    return (
        safe_int(defense_field.get("base"), 0),
        safe_int(defense_field.get("max"), 0),
        safe_int(defense_field.get("augmented"), 0),
    )


def extract_slots(slots_field):
    """
    mhw-db usually provides:
      slots: [{ "rank": 1 }, { "rank": 2 }, ...]

    MVP policy:
    - store only top 3 ranks
    - missing slots become 0
    - tolerate mixed formats defensively
    """
    slot_vals = [0, 0, 0]

    if slots_field is None:
        return tuple(slot_vals)

    if isinstance(slots_field, dict):
        slots_field = [slots_field]

    if not isinstance(slots_field, list):
        return tuple(slot_vals)

    ranks = []
    for s in slots_field:
        if isinstance(s, dict):
            ranks.append(safe_int(s.get("rank"), 0))
        else:
            # sometimes it might already be an int
            ranks.append(safe_int(s, 0))

    # keep only first 3, fill rest with 0
    for i in range(min(3, len(ranks))):
        slot_vals[i] = max(0, ranks[i])

    return tuple(slot_vals)


def derive_skill_max_level(skill_dict):
    """
    If the skill dict includes ranks, derive max level similarly to import_skills.
    Otherwise fall back to 1.

    mhw-db typical:
      skill: { id, name, description, ranks:[{level:1},...] }
    """
    if not isinstance(skill_dict, dict):
        return 1

    ranks = skill_dict.get("ranks")
    if ranks is None:
        return 1

    if isinstance(ranks, dict):
        ranks = [ranks]

    if not isinstance(ranks, list) or not ranks:
        return 1

    levels = []
    for r in ranks:
        if not isinstance(r, dict):
            continue
        lvl = r.get("level")
        try:
            if lvl is not None:
                levels.append(int(lvl))
        except (ValueError, TypeError):
            continue

    if levels:
        return max(levels)

    return max(1, len(ranks))


def extract_armor_skills(armor_dict):
    """
    mhw-db usually provides:
      skills: [
        { "skill": { ...skillFields... }, "level": 1 },
        ...
      ]

    Return a list of tuples: (skill_dict, level_int)
    """
    if not isinstance(armor_dict, dict):
        return []

    skills_field = armor_dict.get("skills")
    if skills_field is None:
        return []

    if isinstance(skills_field, dict):
        skills_field = [skills_field]

    if not isinstance(skills_field, list):
        return []

    out = []
    for entry in skills_field:
        if not isinstance(entry, dict):
            continue
        skill_dict = entry.get("skill")
        level = safe_int(entry.get("level"), 1)
        if isinstance(skill_dict, dict):
            out.append((skill_dict, max(1, level)))

    return out


# ==================================================
# Command
# ==================================================
class Command(BaseCommand):
    help = "Import MHW armor data into the internal database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--armors",
            type=str,
            required=True,
            help="Path to armors JSON file",
        )

        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing armors (and their ArmorSkill links) before importing",
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
            help="Limit number of armors to import (0 = no limit)",
        )

    def handle(self, *args, **options):
        path = options["armors"]
        reset = options["reset"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        armors = extract_armor_list(payload)
        if not armors:
            self.stdout.write(self.style.ERROR("Invalid JSON: could not find a list of armors"))
            return

        if limit and limit > 0:
            armors = armors[:limit]

        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        armor_skills_created = 0
        armor_skills_deleted = 0
        skills_created = 0
        skills_updated = 0

        with transaction.atomic():
            if reset and not dry_run:
                # Delete join rows first (safe), then armors.
                ArmorSkill.objects.all().delete()
                Armor.objects.all().delete()

            for idx, a in enumerate(armors, start=1):
                if not isinstance(a, dict):
                    skipped_count += 1
                    continue

                try:
                    external_id = pick_external_id(a)
                    name = a.get("name")
                    armor_type = normalize_armor_type(a.get("type") or a.get("armor_type"))
                    rarity = safe_int(a.get("rarity"), 1)

                    defense_base, defense_max, defense_aug = extract_defense(a.get("defense"))
                    slot_1, slot_2, slot_3 = extract_slots(a.get("slots"))

                    if external_id is None or not name or not armor_type:
                        skipped_count += 1
                        continue

                    if dry_run:
                        # still count as "would create"
                        created_count += 1
                        continue

                    obj, created = Armor.objects.get_or_create(
                        external_id=int(external_id),
                        defaults={
                            "name": name,
                            "armor_type": armor_type,
                            "rarity": rarity,
                            "defense_base": defense_base,
                            "defense_max": defense_max,
                            "defense_augmented": defense_aug,
                            "slot_1": slot_1,
                            "slot_2": slot_2,
                            "slot_3": slot_3,
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        changed = False

                        if obj.name != name:
                            obj.name = name
                            changed = True

                        if obj.armor_type != armor_type:
                            obj.armor_type = armor_type
                            changed = True

                        if obj.rarity != rarity:
                            obj.rarity = rarity
                            changed = True

                        if obj.defense_base != defense_base:
                            obj.defense_base = defense_base
                            changed = True

                        if obj.defense_max != defense_max:
                            obj.defense_max = defense_max
                            changed = True

                        if obj.defense_augmented != defense_aug:
                            obj.defense_augmented = defense_aug
                            changed = True

                        if obj.slot_1 != slot_1:
                            obj.slot_1 = slot_1
                            changed = True

                        if obj.slot_2 != slot_2:
                            obj.slot_2 = slot_2
                            changed = True

                        if obj.slot_3 != slot_3:
                            obj.slot_3 = slot_3
                            changed = True

                        if changed:
                            obj.save()
                            updated_count += 1

                    # --------------------------------------------------
                    # Armor skills (replace policy)
                    # --------------------------------------------------
                    # MVP policy:
                    # - for each armor, we "replace" skills:
                    #   delete existing ArmorSkill rows for that armor, then recreate.
                    existing_qs = ArmorSkill.objects.filter(armor=obj)
                    deleted = existing_qs.count()
                    if deleted:
                        existing_qs.delete()
                        armor_skills_deleted += deleted

                    pairs = extract_armor_skills(a)

                    for skill_dict, level in pairs:
                        skill_external_id = pick_external_id(skill_dict)
                        skill_name = skill_dict.get("name")
                        skill_desc = skill_dict.get("description") or ""
                        skill_max_level = derive_skill_max_level(skill_dict)

                        if skill_external_id is None or not skill_name:
                            # Skip malformed skill entries
                            continue

                        skill_obj, skill_created = Skill.objects.get_or_create(
                            external_id=int(skill_external_id),
                            defaults={
                                "name": skill_name,
                                "description": skill_desc,
                                "max_level": int(skill_max_level),
                            },
                        )
                        if skill_created:
                            skills_created += 1
                        else:
                            skill_changed = False

                            if skill_obj.name != skill_name:
                                skill_obj.name = skill_name
                                skill_changed = True

                            # Keep description updated if source provides it
                            if (skill_obj.description or "") != (skill_desc or ""):
                                skill_obj.description = skill_desc
                                skill_changed = True

                            # Only update max_level if new value is higher (safer)
                            try:
                                new_ml = int(skill_max_level)
                                if new_ml > int(skill_obj.max_level):
                                    skill_obj.max_level = new_ml
                                    skill_changed = True
                            except (ValueError, TypeError):
                                pass

                            if skill_changed:
                                skill_obj.save()
                                skills_updated += 1

                        ArmorSkill.objects.create(
                            armor=obj,
                            skill=skill_obj,
                            level=max(1, int(level)),
                        )
                        armor_skills_created += 1

                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.WARNING(f"[{idx}] Failed armor import: {e}"))
                    continue

        self.stdout.write(self.style.SUCCESS("Armor import completed."))
        self.stdout.write(f"Armors created: {created_count}")
        self.stdout.write(f"Armors updated: {updated_count}")
        self.stdout.write(f"Armors skipped: {skipped_count}")
        self.stdout.write(f"Armors failed: {failed_count}")
        self.stdout.write(f"ArmorSkill links created: {armor_skills_created}")
        self.stdout.write(f"ArmorSkill links deleted: {armor_skills_deleted}")
        self.stdout.write(f"Skills created (from armor payload): {skills_created}")
        self.stdout.write(f"Skills updated (from armor payload): {skills_updated}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode: no DB changes were made."))