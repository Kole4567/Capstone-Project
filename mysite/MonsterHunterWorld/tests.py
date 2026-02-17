import json
import os
import tempfile

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from .models import (
    Monster,
    MonsterWeakness,
    Weapon,
    Skill,
    Armor,
    ArmorSkill,
    Build,
    BuildArmorPiece,
    Decoration,
    DecorationSkill,
    BuildDecoration,
)


# ==================================================
# Monsters: import pipeline + API (deterministic via temp JSON)
# ==================================================
class MHWImportAndAPITests(TestCase):
    """
    Deterministic tests for:
    - import_mhw pipeline sanity (monsters + weaknesses)
    - monsters endpoints (list/paged/detail)
    - minimal filters

    Notes
    - Does NOT depend on repo-tracked JSON files.
    - Generates a tiny mhw-db-like payload in a temp file.
    """

    @classmethod
    def setUpTestData(cls):
        payload = [
            {
                "id": 999001,
                "name": "Test Monster A",
                "species": "Elder Dragon",
                "weaknesses": [
                    {"element": "fire", "stars": 3, "condition": None},
                    {"element": "water", "stars": 1, "condition": "only when enraged"},
                ],
            },
            {
                "id": 999002,
                "name": "Test Monster B",
                "species": "Flying Wyvern",
                "weaknesses": [
                    {"element": "thunder", "stars": 2},
                ],
            },
        ]

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                delete=False,
                encoding="utf-8",
            ) as f:
                json.dump(payload, f)
                temp_path = f.name

            call_command("import_mhw", monsters=temp_path, reset=True)

            if Monster.objects.count() == 0:
                raise AssertionError("import_mhw did not populate Monster table in tests.")

        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def setUp(self):
        self.client = APIClient()

    # ------------------------------------------------------------
    # Import sanity
    # ------------------------------------------------------------
    def test_import_populates_monsters(self):
        self.assertGreater(Monster.objects.count(), 0)

    def test_import_populates_weaknesses(self):
        self.assertGreater(MonsterWeakness.objects.count(), 0)

    # ------------------------------------------------------------
    # API endpoints
    # ------------------------------------------------------------
    def test_monsters_list_endpoint(self):
        resp = self.client.get("/api/v1/mhw/monsters/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        first = data[0]
        self.assertIn("id", first)
        self.assertIn("external_id", first)
        self.assertIn("name", first)
        self.assertIn("monster_type", first)
        self.assertIn("is_elder_dragon", first)

    def test_monsters_paged_endpoint(self):
        resp = self.client.get("/api/v1/mhw/monsters/paged/?limit=10&offset=0")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIn("count", data)
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
        self.assertLessEqual(len(data["results"]), 10)

    def test_monster_detail_endpoint(self):
        monster = Monster.objects.order_by("id").first()
        self.assertIsNotNone(monster)

        resp = self.client.get(f"/api/v1/mhw/monsters/{monster.id}/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIn("id", data)
        self.assertIn("external_id", data)
        self.assertIn("name", data)
        self.assertIn("monster_type", data)
        self.assertIn("is_elder_dragon", data)
        self.assertIn("weaknesses", data)
        self.assertIsInstance(data["weaknesses"], list)

    # ------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------
    def test_filter_is_elder_dragon(self):
        resp = self.client.get("/api/v1/mhw/monsters/?is_elder_dragon=true")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        for m in data:
            self.assertTrue(m.get("is_elder_dragon"))

    def test_filter_element_and_min_stars(self):
        resp = self.client.get("/api/v1/mhw/monsters/?element=Fire&min_stars=2")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)

        # Ensure no duplicates due to joins
        ids = [m["id"] for m in data if "id" in m]
        self.assertEqual(len(ids), len(set(ids)))

    def test_invalid_min_stars_is_ignored(self):
        resp = self.client.get("/api/v1/mhw/monsters/?element=Fire&min_stars=999")
        self.assertEqual(resp.status_code, 200)


# ==================================================
# Weapons API tests (deterministic, no import file required)
# ==================================================
class WeaponAPITests(TestCase):
    """
    Deterministic weapons tests:
    - list/paged/detail
    - filters: weapon_type, element, rarity range
    - ordering (if supported)
    """

    @classmethod
    def setUpTestData(cls):
        Weapon.objects.create(
            external_id=900001,
            name="Test Weapon A",
            weapon_type="long-sword",
            rarity=6,
            attack_raw=660,
            attack_display=660,
            affinity=0,
            element="Fire",
            element_damage=120,
            elderseal=None,
        )
        Weapon.objects.create(
            external_id=900002,
            name="Test Weapon B",
            weapon_type="long-sword",
            rarity=8,
            attack_raw=770,
            attack_display=770,
            affinity=10,
            element="Ice",
            element_damage=150,
            elderseal=None,
        )
        Weapon.objects.create(
            external_id=900003,
            name="Test Weapon C",
            weapon_type="hammer",
            rarity=7,
            attack_raw=820,
            attack_display=820,
            affinity=-10,
            element=None,
            element_damage=None,
            elderseal=None,
        )

    def setUp(self):
        self.client = APIClient()

    def test_weapons_list_returns_array(self):
        resp = self.client.get("/api/v1/mhw/weapons/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 3)

    def test_weapons_paged_returns_paginated_shape(self):
        resp = self.client.get("/api/v1/mhw/weapons/paged/?limit=2&offset=0")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, dict)
        self.assertIn("count", data)
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
        self.assertLessEqual(len(data["results"]), 2)

    def test_weapons_filter_by_weapon_type(self):
        resp = self.client.get("/api/v1/mhw/weapons/?weapon_type=long-sword")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)
        for w in data:
            self.assertEqual(w["weapon_type"], "long-sword")

    def test_weapons_filter_by_element_case_insensitive(self):
        resp = self.client.get("/api/v1/mhw/weapons/?element=fire")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        for w in data:
            self.assertIsNotNone(w.get("element"))
            self.assertEqual(w["element"].lower(), "fire")

    def test_weapons_filter_by_rarity_range(self):
        resp = self.client.get("/api/v1/mhw/weapons/?min_rarity=7&max_rarity=8")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)
        for w in data:
            self.assertGreaterEqual(int(w["rarity"]), 7)
            self.assertLessEqual(int(w["rarity"]), 8)

    def test_weapons_detail_endpoint(self):
        weapon = Weapon.objects.get(external_id=900001)
        resp = self.client.get(f"/api/v1/mhw/weapons/{weapon.id}/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["id"], weapon.id)
        self.assertEqual(data["external_id"], 900001)
        self.assertEqual(data["name"], "Test Weapon A")
        self.assertEqual(data["weapon_type"], "long-sword")
        self.assertEqual(int(data["rarity"]), 6)


# ==================================================
# Skills API tests (deterministic, no import file required)
# ==================================================
class SkillAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Skill.objects.create(
            external_id=910001,
            name="Attack Boost",
            description="Increases attack power.",
            max_level=7,
        )
        Skill.objects.create(
            external_id=910002,
            name="Health Boost",
            description="Increases health.",
            max_level=3,
        )
        Skill.objects.create(
            external_id=910003,
            name="Critical Eye",
            description="Increases affinity.",
            max_level=7,
        )

    def setUp(self):
        self.client = APIClient()

    def test_skills_list_returns_array(self):
        resp = self.client.get("/api/v1/mhw/skills/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 3)

        first = data[0]
        self.assertIn("id", first)
        self.assertIn("external_id", first)
        self.assertIn("name", first)
        self.assertIn("description", first)
        self.assertIn("max_level", first)

    def test_skills_paged_returns_paginated_shape(self):
        resp = self.client.get("/api/v1/mhw/skills/paged/?limit=2&offset=0")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, dict)
        self.assertIn("count", data)
        self.assertIn("results", data)

    def test_skills_detail_endpoint(self):
        skill = Skill.objects.get(external_id=910001)
        resp = self.client.get(f"/api/v1/mhw/skills/{skill.id}/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["id"], skill.id)
        self.assertEqual(data["external_id"], 910001)
        self.assertEqual(data["name"], "Attack Boost")
        self.assertIn("max_level", data)

    def test_skills_filter_name_contains(self):
        resp = self.client.get("/api/v1/mhw/skills/?name=attack")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        for s in data:
            self.assertIn("attack", s["name"].lower())


# ==================================================
# Armors API tests (deterministic, no import file required)
# ==================================================
class ArmorAPITests(TestCase):
    """
    Validates:
    - list returns array (lightweight)
    - paged returns {count, results}
    - detail includes nested armor_skills + armor_set
    - filters: armor_type, rarity range, min_defense, has_skill (if supported)
    """

    @classmethod
    def setUpTestData(cls):
        attack = Skill.objects.create(
            external_id=920001,
            name="Attack Boost",
            description="Increases attack power.",
            max_level=7,
        )
        health = Skill.objects.create(
            external_id=920002,
            name="Health Boost",
            description="Increases health.",
            max_level=3,
        )

        a1 = Armor.objects.create(
            external_id=930001,
            name="Test Helm A",
            armor_type="head",
            rarity=6,
            defense_base=60,
            defense_max=80,
            defense_augmented=90,
            slot_1=1,
            slot_2=0,
            slot_3=0,
            res_fire=2,
            res_water=0,
            res_thunder=0,
            res_ice=0,
            res_dragon=0,
            armor_set_external_id=100,
            armor_set_name="Test Set",
            armor_set_rank="low",
            armor_set_bonus_external_id=None,
        )

        a2 = Armor.objects.create(
            external_id=930002,
            name="Test Chest A",
            armor_type="chest",
            rarity=8,
            defense_base=72,
            defense_max=92,
            defense_augmented=102,
            slot_1=2,
            slot_2=1,
            slot_3=0,
            res_fire=1,
            res_water=1,
            res_thunder=0,
            res_ice=0,
            res_dragon=0,
            armor_set_external_id=100,
            armor_set_name="Test Set",
            armor_set_rank="low",
            armor_set_bonus_external_id=None,
        )

        ArmorSkill.objects.create(armor=a1, skill=attack, level=1)
        ArmorSkill.objects.create(armor=a2, skill=attack, level=2)
        ArmorSkill.objects.create(armor=a2, skill=health, level=1)

    def setUp(self):
        self.client = APIClient()

    def test_armor_list_returns_array(self):
        resp = self.client.get("/api/v1/mhw/armors/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)

        first = data[0]
        self.assertIn("id", first)
        self.assertIn("external_id", first)
        self.assertIn("name", first)
        self.assertIn("armor_type", first)
        self.assertIn("rarity", first)
        self.assertIn("defense_base", first)
        self.assertIn("slot_1", first)
        self.assertNotIn("armor_skills", first)  # list should be lightweight

    def test_armor_paged_returns_paginated_shape(self):
        resp = self.client.get("/api/v1/mhw/armors/paged/?limit=1&offset=0")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, dict)
        self.assertIn("count", data)
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_armor_detail_includes_nested_skills_and_armor_set(self):
        armor = Armor.objects.get(external_id=930002)
        resp = self.client.get(f"/api/v1/mhw/armors/{armor.id}/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["external_id"], 930002)

        self.assertIn("armor_skills", data)
        self.assertIsInstance(data["armor_skills"], list)
        self.assertGreaterEqual(len(data["armor_skills"]), 1)

        entry = data["armor_skills"][0]
        self.assertIn("skill", entry)
        self.assertIn("level", entry)
        self.assertIsInstance(entry["skill"], dict)
        self.assertIn("name", entry["skill"])
        self.assertIn("max_level", entry["skill"])

        self.assertIn("armor_set", data)
        self.assertIsInstance(data["armor_set"], dict)
        self.assertIn("external_id", data["armor_set"])
        self.assertIn("name", data["armor_set"])
        self.assertIn("rank", data["armor_set"])

    def test_armor_filter_by_armor_type(self):
        resp = self.client.get("/api/v1/mhw/armors/?armor_type=head")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        for a in data:
            self.assertEqual(a["armor_type"], "head")

    def test_armor_filter_by_rarity_range(self):
        resp = self.client.get("/api/v1/mhw/armors/?min_rarity=7&max_rarity=8")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        for a in data:
            self.assertGreaterEqual(int(a["rarity"]), 7)
            self.assertLessEqual(int(a["rarity"]), 8)

    def test_armor_filter_by_min_defense(self):
        resp = self.client.get("/api/v1/mhw/armors/?min_defense=70")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        for a in data:
            self.assertGreaterEqual(int(a["defense_base"]), 70)

    def test_armor_filter_has_skill_no_duplicates(self):
        # If your view supports has_skill filter, this validates no duplicates from joins.
        resp = self.client.get("/api/v1/mhw/armors/?has_skill=attack")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)

        ids = [a["id"] for a in data if "id" in a]
        self.assertEqual(len(ids), len(set(ids)))


# ==================================================
# Builds + BuildStats tests (THIS IS THE NEW IMPORTANT PART)
# ==================================================
class BuildAndStatsAPITests(TestCase):
    """
    Verifies:
    - PATCH build with weapon_external_id
    - PATCH build with armors dict (slot -> armor_external_id)
    - GET build detail returns weapon + armor_pieces
    - GET stats aggregates:
        weapon attack
        total defense
        total resistances
        skill list + sources
    """

    @classmethod
    def setUpTestData(cls):
        # Skill for armor
        hunger = Skill.objects.create(
            external_id=429,
            name="Hunger Resistance",
            description="Slows down stamina depletion.",
            max_level=3,
        )

        # Weapon (matches your real sample: attack_raw=80, attack_display=384)
        Weapon.objects.create(
            id=1,  # keep stable for debugging (optional)
            external_id=1,
            name="Buster Sword 1",
            weapon_type="great-sword",
            rarity=1,
            attack_raw=80,
            attack_display=384,
            element=None,
            element_damage=None,
            affinity=0,
            elderseal=None,
        )

        # Armors (Leather style) with resistances that sum to fire=10 and defense=10
        # 5 pieces, each defense_base=2, res_fire=2 => total defense=10, fire=10
        pieces = [
            (1, "Leather Headgear", "head"),
            (2, "Leather Mail", "chest"),
            (3, "Leather Gloves", "gloves"),
            (4, "Leather Belt", "waist"),
            (5, "Leather Trousers", "legs"),
        ]

        armor_objs = []
        for ext_id, name, a_type in pieces:
            armor_objs.append(
                Armor.objects.create(
                    external_id=ext_id,
                    name=name,
                    armor_type=a_type,
                    rarity=1,
                    defense_base=2,
                    defense_max=0,
                    defense_augmented=0,
                    slot_1=0,
                    slot_2=0,
                    slot_3=0,
                    res_fire=2,
                    res_water=0,
                    res_thunder=0,
                    res_ice=0,
                    res_dragon=0,
                    armor_set_external_id=200,
                    armor_set_name="Leather",
                    armor_set_rank="low",
                    armor_set_bonus_external_id=None,
                )
            )

        # Attach 1 skill to head only (level 1)
        head = Armor.objects.get(external_id=1)
        ArmorSkill.objects.create(armor=head, skill=hunger, level=1)

        # Decoration (optional future coverage) - keep minimal but valid if endpoint expects empty list ok
        deco = Decoration.objects.create(
            external_id=5001,
            name="Test Jewel",
            rarity=5,
        )
        DecorationSkill.objects.create(
            decoration=deco,
            skill=hunger,
            level=1,
        )

        # Create a build
        cls.build = Build.objects.create(
            name="test build",
            description="stats integration test",
            weapon=None,
            charm=None,
        )

    def setUp(self):
        self.client = APIClient()

    def test_patch_build_weapon_external_id(self):
        resp = self.client.patch(
            f"/api/v1/mhw/builds/{self.build.id}/",
            data={"weapon_external_id": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIn("weapon", data)
        self.assertIsNotNone(data["weapon"])
        self.assertEqual(data["weapon"]["external_id"], 1)
        self.assertEqual(data["weapon"]["attack_raw"], 80)
        self.assertEqual(data["weapon"]["attack_display"], 384)

    def test_patch_build_armors_dict_and_stats_aggregation(self):
        # 1) set weapon
        resp = self.client.patch(
            f"/api/v1/mhw/builds/{self.build.id}/",
            data={"weapon_external_id": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)

        # 2) set armors using MHW-style dict
        resp = self.client.patch(
            f"/api/v1/mhw/builds/{self.build.id}/",
            data={
                "armors": {
                    "head": 1,
                    "chest": 2,
                    "gloves": 3,
                    "waist": 4,
                    "legs": 5,
                }
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)

        # 3) build detail should show 5 armor pieces
        detail = self.client.get(f"/api/v1/mhw/builds/{self.build.id}/")
        self.assertEqual(detail.status_code, 200)
        d = detail.json()
        self.assertIn("armor_pieces", d)
        self.assertEqual(len(d["armor_pieces"]), 5)

        # 4) stats should aggregate weapon + armor totals
        stats = self.client.get(f"/api/v1/mhw/builds/{self.build.id}/stats/")
        self.assertEqual(stats.status_code, 200)
        s = stats.json()

        self.assertEqual(s["build_id"], self.build.id)

        self.assertIn("stats", s)
        self.assertIn("attack", s["stats"])
        self.assertEqual(int(s["stats"]["attack"]["raw"]), 80)
        self.assertEqual(int(s["stats"]["attack"]["display"]), 384)

        self.assertEqual(int(s["stats"]["defense"]), 10)

        self.assertIn("resistances", s["stats"])
        self.assertEqual(int(s["stats"]["resistances"]["fire"]), 10)
        self.assertEqual(int(s["stats"]["resistances"]["water"]), 0)

        # skills should include Hunger Resistance level 1 sourced from armor
        self.assertIn("skills", s)
        self.assertIsInstance(s["skills"], list)
        self.assertGreaterEqual(len(s["skills"]), 1)

        found = [x for x in s["skills"] if x.get("skill_id") == 429]
        self.assertTrue(found, "Expected skill_id=429 in build stats skills")

        skill_entry = found[0]
        self.assertEqual(skill_entry["name"], "Hunger Resistance")
        self.assertEqual(int(skill_entry["level"]), 1)
        self.assertEqual(int(skill_entry["max_level"]), 3)

        self.assertIn("sources", skill_entry)
        self.assertIn("armor", skill_entry["sources"])
        self.assertEqual(int(skill_entry["sources"]["armor"]), 1)

        # set_bonuses exists (even if placeholder/inactive)
        self.assertIn("set_bonuses", s)
        self.assertIsInstance(s["set_bonuses"], list)