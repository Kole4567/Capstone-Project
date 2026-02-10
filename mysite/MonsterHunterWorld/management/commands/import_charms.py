import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from MonsterHunterWorld.models import Charm, CharmSkill, Skill


def _load_json(path: Path):
    if not path.exists():
        raise CommandError(f"File not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CommandError(f"Invalid JSON in {path}: {e}")


def _coerce_int(val, default=None):
    try:
        if val is None:
            return default
        return int(val)
    except (TypeError, ValueError):
        return default


class Command(BaseCommand):
    help = "Import charms from mhw-db API JSON (supports Charm.ranks format)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            required=True,
            help="Path to charms JSON file (e.g., data/mhw_charms_raw.json).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all Charm and CharmSkill rows before importing.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"]).expanduser().resolve()
        reset = bool(options["reset"])

        payload = _load_json(path)

        # Expected shapes:
        # - mhw-db API: [ { id, name, ranks: [...] }, ... ]
        # - also accept: { "charms": [ ... ] }
        if isinstance(payload, dict):
            charms_data = payload.get("charms", [])
        elif isinstance(payload, list):
            charms_data = payload
        else:
            raise CommandError("Unsupported JSON shape: expected dict or list.")

        if reset:
            self.stdout.write("Reset enabled: deleting CharmSkill and Charm...")
            CharmSkill.objects.all().delete()
            Charm.objects.all().delete()

        # Skill.external_id -> Skill.id
        skill_by_external = {s.external_id: s.id for s in Skill.objects.all()}

        created_count = 0
        updated_count = 0
        skipped_count = 0
        skills_linked = 0
        skills_skipped = 0

        for charm_obj in charms_data:
            if not isinstance(charm_obj, dict):
                skipped_count += 1
                continue

            base_id = _coerce_int(charm_obj.get("id"))
            base_name = (charm_obj.get("name") or "").strip()

            if base_id is None or not base_name:
                skipped_count += 1
                continue

            ranks = charm_obj.get("ranks") or []
            if not isinstance(ranks, list) or len(ranks) == 0:
                skipped_count += 1
                continue

            for rank in ranks:
                if not isinstance(rank, dict):
                    skipped_count += 1
                    continue

                level = _coerce_int(rank.get("level"))
                rarity = _coerce_int(rank.get("rarity"), default=None)

                if level is None:
                    skipped_count += 1
                    continue

                # Make a stable unique int external_id per rank
                # Assumption: level < 100 (true for MHW charms)
                external_id = base_id * 100 + level
                name = f"{base_name} Lv {level}"

                charm, created = Charm.objects.update_or_create(
                    external_id=external_id,
                    defaults={
                        "name": name,
                        "rarity": rarity,
                    },
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                # Replace semantics for charm skills
                CharmSkill.objects.filter(charm=charm).delete()

                skills = rank.get("skills") or []
                if not isinstance(skills, list):
                    skills = []

                # mhw-db rank skill entry example:
                # { "skill": 15, "level": 1, ... }
                for entry in skills:
                    if not isinstance(entry, dict):
                        skills_skipped += 1
                        continue

                    skill_external_id = _coerce_int(entry.get("skill"))
                    skill_level = _coerce_int(entry.get("level"), default=1)
                    skill_level = max(skill_level, 1)

                    if skill_external_id is None:
                        skills_skipped += 1
                        continue

                    skill_id = skill_by_external.get(skill_external_id)
                    if not skill_id:
                        # Skill not imported yet; skip safely
                        skills_skipped += 1
                        continue

                    CharmSkill.objects.create(
                        charm=charm,
                        skill_id=skill_id,
                        level=skill_level,
                    )
                    skills_linked += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Charms import complete. "
                f"created={created_count}, updated={updated_count}, skipped={skipped_count}, "
                f"skills_linked={skills_linked}, skills_skipped={skills_skipped}"
            )
        )