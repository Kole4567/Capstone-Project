import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from MonsterHunterWorld.models import Decoration, DecorationSkill, Skill


class Command(BaseCommand):
    help = "Import MHW decorations data from a mhw-db style JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            required=True,
            help="Path to a JSON file (mhw-db decorations endpoint response).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing Decoration/DecorationSkill before importing.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate only (no DB writes).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of records processed (for local testing).",
        )

    def handle(self, *args, **options):
        path = options["path"]
        reset = options["reset"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        file_path = Path(path)
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path.resolve()}")

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise CommandError(f"Failed to read JSON: {e}")

        if not isinstance(data, list):
            raise CommandError("Expected a JSON array (list) at the top level.")

        if limit is not None:
            data = data[: max(0, limit)]

        if reset and not dry_run:
            self.stdout.write("Reset enabled: deleting DecorationSkill and Decoration...")
            DecorationSkill.objects.all().delete()
            Decoration.objects.all().delete()

        created = 0
        updated = 0
        skipped = 0
        skills_linked = 0
        skills_skipped = 0

        for idx, row in enumerate(data, start=1):
            if not isinstance(row, dict):
                skipped += 1
                continue

            external_id = row.get("id")
            name = row.get("name")
            rarity = row.get("rarity")

            if external_id is None or name is None:
                skipped += 1
                continue

            try:
                external_id = int(external_id)
            except (TypeError, ValueError):
                skipped += 1
                continue

            # rarity sometimes may be missing; keep it defensive
            try:
                rarity_val = int(rarity) if rarity is not None else 1
            except (TypeError, ValueError):
                rarity_val = 1

            skills_payload = row.get("skills") or []
            if not isinstance(skills_payload, list):
                skills_payload = []

            if dry_run:
                # Validate parse only
                for s in skills_payload:
                    if not isinstance(s, dict):
                        continue
                    skill_info = s.get("skill") or {}
                    skill_external_id = skill_info.get("id")
                    _ = s.get("level")
                    _ = skill_external_id
                continue

            with transaction.atomic():
                obj, was_created = Decoration.objects.get_or_create(
                    external_id=external_id,
                    defaults={"name": name, "rarity": rarity_val},
                )

                changed = False
                if obj.name != name:
                    obj.name = name
                    changed = True
                if obj.rarity != rarity_val:
                    obj.rarity = rarity_val
                    changed = True

                if was_created:
                    created += 1
                else:
                    if changed:
                        obj.save(update_fields=["name", "rarity"])
                        updated += 1

                # Replace semantics for join rows per decoration
                DecorationSkill.objects.filter(decoration=obj).delete()

                for s in skills_payload:
                    if not isinstance(s, dict):
                        continue

                    level = s.get("level", 1)
                    try:
                        level = int(level)
                    except (TypeError, ValueError):
                        level = 1

                    skill_info = s.get("skill") or {}
                    if not isinstance(skill_info, dict):
                        skills_skipped += 1
                        continue

                    # mhw-db skill id maps to our Skill.external_id
                    skill_external_id = skill_info.get("id")
                    try:
                        skill_external_id = int(skill_external_id)
                    except (TypeError, ValueError):
                        skills_skipped += 1
                        continue

                    skill_obj = Skill.objects.filter(external_id=skill_external_id).first()
                    if not skill_obj:
                        skills_skipped += 1
                        continue

                    DecorationSkill.objects.create(
                        decoration=obj,
                        skill=skill_obj,
                        level=max(1, level),
                    )
                    skills_linked += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry-run complete. No DB writes performed."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                "Decorations import complete. "
                f"created={created}, updated={updated}, skipped={skipped}, "
                f"skills_linked={skills_linked}, skills_skipped={skills_skipped}"
            )
        )
    