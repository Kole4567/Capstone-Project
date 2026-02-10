import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from MonsterHunterWorld.models import Decoration, DecorationSkill, Skill


class Command(BaseCommand):
    help = "Import Decorations from mhw-db JSON (https://mhw-db.com/decorations)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            required=True,
            help="Path to decorations JSON file (list). Example: data/mhw_decorations_raw.json",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete DecorationSkill and Decoration before importing.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate without writing to the database.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of records for quick testing.",
        )

    def handle(self, *args, **options):
        path = Path(options["path"]).resolve()
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        reset = options["reset"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        if reset and not dry_run:
            self.stdout.write("Reset enabled: deleting DecorationSkill and Decoration...")
            DecorationSkill.objects.all().delete()
            Decoration.objects.all().delete()

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise CommandError(f"Failed to load JSON: {e}")

        if not isinstance(data, list):
            raise CommandError("Expected a JSON list for decorations.")

        if limit is not None:
            data = data[: max(0, int(limit))]

        created = 0
        updated = 0
        skipped = 0
        skills_linked = 0
        skills_skipped = 0

        for row in data:
            external_id = row.get("id")
            name = (row.get("name") or "").strip()
            rarity = row.get("rarity")
            slot = row.get("slot")  # optional, kept for future use
            skills = row.get("skills") or []

            if external_id is None or not name:
                skipped += 1
                continue

            # rarity can be missing in edge cases
            try:
                rarity = int(rarity) if rarity is not None else 1
            except ValueError:
                rarity = 1

            if dry_run:
                # Validate skills structure without writing
                for s in skills:
                    # In your JSON, both "skill" and "id" exist. Prefer "skill".
                    skill_external_id = s.get("skill", s.get("id"))
                    level = s.get("level", 1)
                    try:
                        int(skill_external_id)
                        int(level)
                    except Exception:
                        skills_skipped += 1
                continue

            # Write one decoration + its join rows atomically
            with transaction.atomic():
                obj, was_created = Decoration.objects.update_or_create(
                    external_id=int(external_id),
                    defaults={
                        "name": name,
                        "rarity": rarity,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

                # Replace semantics for join rows
                DecorationSkill.objects.filter(decoration=obj).delete()

                for s in skills:
                    skill_external_id = s.get("skill", s.get("id"))
                    level = s.get("level", 1)

                    try:
                        skill_external_id = int(skill_external_id)
                        level = int(level)
                    except Exception:
                        skills_skipped += 1
                        continue

                    # Match by Skill.external_id (mhw-db skill id)
                    skill_obj = Skill.objects.filter(external_id=skill_external_id).first()
                    if not skill_obj:
                        # fallback: match by skillName if provided
                        skill_name = (s.get("skillName") or "").strip()
                        if skill_name:
                            skill_obj = Skill.objects.filter(name__iexact=skill_name).first()

                    if not skill_obj:
                        skills_skipped += 1
                        continue

                    DecorationSkill.objects.create(
                        decoration=obj,
                        skill=skill_obj,
                        level=max(1, level),
                    )
                    skills_linked += 1

        self.stdout.write(
            f"Decorations import complete. created={created}, updated={updated}, skipped={skipped}, "
            f"skills_linked={skills_linked}, sklls_skipped={skills_skipped}"
        )