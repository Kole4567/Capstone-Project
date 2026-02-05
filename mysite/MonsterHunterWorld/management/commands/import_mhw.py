import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from MonsterHunterWorld.models import Monster, MonsterWeakness


class Command(BaseCommand):
    help = "Import Monster + Weakness data into local DB (minimal version)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--monsters",
            type=str,
            required=True,
            help="Path to monsters.json file",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        monsters_path = Path(options["monsters"]).expanduser()

        if not monsters_path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {monsters_path}"))
            return

        with monsters_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        created_monsters = 0
        created_weaknesses = 0

        # NOTE: This is a template. We will map actual mhw-db JSON shape next.
        # Expected future format example (we'll adjust to your real file):
        # [
        #   {
        #     "external_id": 1,
        #     "name": "Great Jagras",
        #     "monster_type": "Fanged Wyvern",
        #     "is_elder_dragon": false,
        #     "weaknesses": [
        #       {"kind": "element", "name": "Fire", "stars": 2, "condition": null}
        #     ]
        #   }
        # ]

        for item in data:
            monster, m_created = Monster.objects.get_or_create(
                external_id=item.get("external_id"),
                defaults={
                    "name": item["name"],
                    "monster_type": item.get("monster_type", ""),
                    "is_elder_dragon": bool(item.get("is_elder_dragon", False)),
                },
            )
            if m_created:
                created_monsters += 1

            for w in item.get("weaknesses", []):
                _, w_created = MonsterWeakness.objects.get_or_create(
                    monster=monster,
                    kind=w["kind"],
                    name=w["name"],
                    stars=int(w["stars"]),
                    condition=w.get("condition"),
                )
                if w_created:
                    created_weaknesses += 1

        self.stdout.write(self.style.SUCCESS("Import completed."))
        self.stdout.write(f"Monsters created: {created_monsters}")
        self.stdout.write(f"Weaknesses created: {created_weaknesses}")