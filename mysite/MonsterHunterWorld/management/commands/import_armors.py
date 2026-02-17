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


def safe_int(v, default=0):
    try:
        if v is None:
            return default
        return int(v)
    except (ValueError, TypeError):
        return default


def pick_external_id(obj):
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


def normalize_armor_type(raw):
    """
    mhw-db armor type is usually: head, chest, gloves, waist, legs.
    Normalize common aliases defensively.
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
    mhw-db provides:
      defense: { "base": 64, "max": 84, "augmented": 94 }
    """
    if not isinstance(defense_field, dict):
        return 0, 0, 0

    return (
        safe_int(defense_field.get("base"), 0),
        safe_int(defense_field.get("max"), 0),
        safe_int(defense_field.get("augmented"), 0),
    )


def extract_resistances(res_field):
    """
    mhw-db provides:
      resistances: { "fire": x, "water": y, "thunder": z, "ice": a, "dragon": b }

    Returns:
      (fire, water, thunder, ice, dragon) ints
    """
    if not isinstance(res_field, dict):
        return 0, 0, 0, 0, 0

    return (
        safe_int(res_field.get("fire"), 0),
        safe_int(res_field.get("water"), 0),
        safe_int(res_field.get("thunder"), 0),
        safe_int(res_field.get("ice"), 0),
        safe_int(res_field.get("dragon"), 0),
    )


def extract_slots(slots_field):
    """
    mhw-db provides:
      slots: [{ "rank": 1 }, { "rank": 2 }, ...]
    Store only first 3 ranks.
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
            ranks.append(safe_int(s, 0))

    for i in range(min(3, len(ranks))):
        slot_vals[i] = max(0, ranks[i])

    return tuple(slot_vals)


def extract_armor_set_fields(armor_dict: dict):
    """
    mhw-db provides:
      armorSet: { id, rank, name, pieces:[...], bonus:<setBonusId or None> }

    Note:
    - SetBonus entities/ranks are imported by import_set_bonuses.py.
    - This importer ONLY stores armor_set_bonus_external_id on Armor.
    """
    if not isinstance(armor_dict, dict):
        return None, None, None, None

    armor_set = armor_dict.get("armorSet")
    if not isinstance(armor_set, dict):
        return None, None, None, None

    set_id = safe_int(armor_set.get("id"), default=None)
    set_name = armor_set.get("name")
    set_rank = armor_set.get("rank")
    bonus_id = safe_int(armor_set.get("bonus"), default=None)

    if set_name is not None:
        set_name = str(set_name).strip() or None

    if set_rank is not None:
        set_rank = str(set_rank).strip().lower() or None

    return set_id, set_name, set_rank, bonus_id


def extract_armor_skills(armor_dict):
    """
    mhw-db armor.skills can be one of:
      A) { "skill": { id, name, description, ranks[...] }, "level": 1 }
      B) { "skill": 15, "level": 1 }   <-- IMPORTANT (many dumps use this)

    Return list of dicts:
      {
        "skill_external_id": int,
        "level": int,
        "skill_payload": Optional[dict]  # present when skill is embedded object
      }
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

        lvl = safe_int(entry.get("level"), 1)
        lvl = max(1, lvl)

        s = entry.get("skill")
        if isinstance(s, dict):
            sid = pick_external_id(s)
            if sid is None:
                continue
            out.append({"skill_external_id": int(sid), "level": lvl, "skill_payload": s})
        else:
            sid = safe_int(s, default=None)
            if sid is None:
                continue
            out.append({"skill_external_id": int(sid), "level": lvl, "skill_payload": None})

    return out


def derive_skill_max_level(skill_payload: dict):
    """
    If embedded skill payload includes ranks, derive max_level.
    Otherwise return 1.
    """
    if not isinstance(skill_payload, dict):
        return 1

    ranks = skill_payload.get("ranks")
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

    return max(levels) if levels else 1


# ==================================================
# Command
# ==================================================
class Command(BaseCommand):
    help = "Import MHW armor data into the internal database."

    def add_arguments(self, parser):
        parser.add_argument("--armors", type=str, required=True, help="Path to armors JSON file")

        parser.add_argument(
            "--reset",
            action="store_true",
            help=(
                "SAFE reset: deletes ArmorSkill rows only (keeps Armor rows so Builds won't break). "
                "Then upserts armors + re-creates ArmorSkill links."
            ),
        )

        parser.add_argument(
            "--hard-reset",
            action="store_true",
            help="DANGEROUS reset: deletes ArmorSkill AND Armor (this can break Builds).",
        )

        parser.add_argument("--dry-run", action="store_true", help="Parse only; do not write to DB")
        parser.add_argument("--limit", type=int, default=0, help="Limit number of armors (0 = no limit)")

    def handle(self, *args, **options):
        path = options["armors"]
        reset = options["reset"]
        hard_reset = options["hard_reset"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        if reset and hard_reset:
            self.stdout.write(self.style.ERROR("Choose only one: --reset OR --hard-reset (not both)."))
            return

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
        skills_missing = 0

        # Fast lookup for Skill by external_id (kept fresh when we create new skills)
        skill_by_external = {s.external_id: s for s in Skill.objects.all()}

        with transaction.atomic():
            if not dry_run:
                if hard_reset:
                    ArmorSkill.objects.all().delete()
                    Armor.objects.all().delete()
                elif reset:
                    # SAFE: do not delete Armor rows
                    ArmorSkill.objects.all().delete()

            for idx, a in enumerate(armors, start=1):
                if not isinstance(a, dict):
                    skipped_count += 1
                    continue

                try:
                    external_id = pick_external_id(a)
                    name = (a.get("name") or "").strip()
                    armor_type = normalize_armor_type(a.get("type") or a.get("armor_type"))
                    rarity = safe_int(a.get("rarity"), 1)

                    defense_base, defense_max, defense_aug = extract_defense(a.get("defense"))
                    slot_1, slot_2, slot_3 = extract_slots(a.get("slots"))

                    # NEW: persist resistances to Armor model fields
                    res_fire, res_water, res_thunder, res_ice, res_dragon = extract_resistances(
                        a.get("resistances")
                    )

                    (
                        armor_set_external_id,
                        armor_set_name,
                        armor_set_rank,
                        armor_set_bonus_external_id,
                    ) = extract_armor_set_fields(a)

                    if external_id is None or not name or not armor_type:
                        skipped_count += 1
                        continue

                    if dry_run:
                        created_count += 1
                        continue

                    obj, created = Armor.objects.update_or_create(
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
                            "res_fire": res_fire,
                            "res_water": res_water,
                            "res_thunder": res_thunder,
                            "res_ice": res_ice,
                            "res_dragon": res_dragon,
                            "armor_set_external_id": armor_set_external_id,
                            "armor_set_name": armor_set_name,
                            "armor_set_rank": armor_set_rank,
                            "armor_set_bonus_external_id": armor_set_bonus_external_id,
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    # --------------------------------------------------
                    # Armor skills (replace policy per armor)
                    # --------------------------------------------------
                    existing_qs = ArmorSkill.objects.filter(armor=obj)
                    deleted = existing_qs.count()
                    if deleted:
                        existing_qs.delete()
                        armor_skills_deleted += deleted

                    skill_entries = extract_armor_skills(a)

                    for entry in skill_entries:
                        skill_external_id = int(entry["skill_external_id"])
                        level = max(1, int(entry["level"]))
                        skill_payload = entry.get("skill_payload")

                        skill_obj = skill_by_external.get(skill_external_id)

                        # If skill payload is embedded, we can upsert Skill defensively
                        if skill_payload is not None:
                            skill_name = (skill_payload.get("name") or "").strip()
                            skill_desc = skill_payload.get("description") or ""
                            skill_max_level = derive_skill_max_level(skill_payload)

                            if skill_name:
                                if skill_obj is None:
                                    skill_obj = Skill.objects.create(
                                        external_id=skill_external_id,
                                        name=skill_name,
                                        description=skill_desc,
                                        max_level=int(skill_max_level),
                                    )
                                    skill_by_external[skill_external_id] = skill_obj
                                    skills_created += 1
                                else:
                                    changed = False
                                    if skill_obj.name != skill_name:
                                        skill_obj.name = skill_name
                                        changed = True
                                    if (skill_obj.description or "") != (skill_desc or ""):
                                        skill_obj.description = skill_desc
                                        changed = True
                                    if int(skill_max_level) > int(skill_obj.max_level):
                                        skill_obj.max_level = int(skill_max_level)
                                        changed = True
                                    if changed:
                                        skill_obj.save()
                                        skills_updated += 1

                        # If still missing, try DB lookup once
                        if skill_obj is None:
                            skill_obj = Skill.objects.filter(external_id=skill_external_id).first()
                            if skill_obj:
                                skill_by_external[skill_external_id] = skill_obj

                        if skill_obj is None:
                            skills_missing += 1
                            continue

                        ArmorSkill.objects.create(armor=obj, skill=skill_obj, level=level)
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
        self.stdout.write(f"Skills missing (no Skill.external_id match): {skills_missing}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN mode: no DB changes were made."))