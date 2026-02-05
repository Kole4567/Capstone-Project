import json
from django.core.management.base import BaseCommand
from MonsterHunterWorld.models import Monster, MonsterWeakness


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

    def handle(self, *args, **options):
        path = options["monsters"]
        reset = options["reset"]

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            self.stdout.write(self.style.ERROR("Invalid JSON: expected an array of monsters"))
            return

        if reset:
            MonsterWeakness.objects.all().delete()
            Monster.objects.all().delete()

        monsters_created = 0
        monsters_updated = 0
        weaknesses_created = 0

        # Detect format using the first item with weaknesses
        is_mhw_db_format = False
        for item in data[:5]:
            w = item.get("weaknesses", [])
            if isinstance(w, list) and len(w) > 0 and isinstance(w[0], dict) and "element" in w[0]:
                is_mhw_db_format = True
                break

        for m in data:
            if is_mhw_db_format:
                # mhw-db fields (common):
                # - id (int)
                # - name (str)
                # - species (str) -> use as monster_type
                # - weaknesses: [{element, stars, condition}, ...]
                external_id = m.get("id")
                name = m.get("name")
                monster_type = m.get("species") or ""
                is_elder_dragon = (monster_type.lower() == "elder dragon")

                if external_id is None or not name:
                    continue

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
                    # Keep the internal DB in sync on re-imports
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

                # Replace weaknesses on every import for clean sync
                MonsterWeakness.objects.filter(monster=monster_obj).delete()

                for w in m.get("weaknesses", []):
                    element = w.get("element")
                    stars = w.get("stars")
                    condition = w.get("condition", None)

                    if not element or stars is None:
                        continue

                    MonsterWeakness.objects.create(
                        monster=monster_obj,
                        kind="element",
                        name=str(element).title(),  # Fire, Water, Thunder...
                        stars=int(stars),
                        condition=condition,
                    )
                    weaknesses_created += 1

            else:
                # Test format fields:
                # - external_id, name, monster_type, is_elder_dragon
                # - weaknesses: [{kind, name, stars, condition}, ...]
                external_id = m.get("external_id")
                name = m.get("name")
                monster_type = m.get("monster_type", "")
                is_elder_dragon = bool(m.get("is_elder_dragon", False))

                if external_id is None or not name:
                    continue

                monster_obj, created = Monster.objects.get_or_create(
                    external_id=int(external_id),
                    defaults={
                        "name": name,
                        "monster_type": monster_type,
                        "is_elder_dragon": is_elder_dragon,
                    },
                )
                if created:
                    monsters_created += 1

                MonsterWeakness.objects.filter(monster=monster_obj).delete()

                for w in m.get("weaknesses", []):
                    MonsterWeakness.objects.create(
                        monster=monster_obj,
                        kind=w.get("kind"),
                        name=w.get("name"),
                        stars=w.get("stars"),
                        condition=w.get("condition"),
                    )
                    weaknesses_created += 1

        self.stdout.write(self.style.SUCCESS("Import completed."))
        self.stdout.write(f"Monsters created: {monsters_created}")
        self.stdout.write(f"Monsters updated: {monsters_updated}")
        self.stdout.write(f"Weaknesses created: {weaknesses_created}")