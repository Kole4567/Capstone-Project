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
        # Minimal mhw-db-like payload that the import_mhw heuristic should recognize
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

            # Fail fast if import didn't populate DB
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
    Weapons API tests that do NOT depend on external JSON imports.

    Why this approach?
    - Deterministic: always the same results
    - Fast: creates only a few rows in the test DB
    - Validates: filters, paging shape, detail endpoint behavior
    """

    @classmethod
    def setUpTestData(cls):
        Weapon.objects.create(
            external_id=900001,
            name="Test Long Sword A",
            weapon_type="Long Sword",
            rarity=6,
            attack_raw=660,
            attack_display=660,
            affinity=0,
            element="Fire",
        )

        Weapon.objects.create(
            external_id=900002,
            name="Test Long Sword B",
            weapon_type="Long Sword",
            rarity=8,
            attack_raw=770,
            attack_display=770,
            affinity=10,
            element="Ice",
        )

        Weapon.objects.create(
            external_id=900003,
            name="Test Hammer A",
            weapon_type="Hammer",
            rarity=7,
            attack_raw=820,
            attack_display=820,
            affinity=-10,
            element=None,
        )

    def setUp(self):
        self.client = APIClient()

    def test_weapons_list_returns_array(self):
        resp = self.client.get("/api/v1/mhw/weapons/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)
        self.assertGreaterEqual(len(resp.json()), 3)

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
        resp = self.client.get("/api/v1/mhw/weapons/?weapon_type=Long%20Sword")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)
        for w in data:
            self.assertEqual(w["weapon_type"], "Long Sword")

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

    def test_weapons_order_by_attack_raw_desc(self):
        resp = self.client.get("/api/v1/mhw/weapons/?order_by=-attack_raw")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 3)

        attacks = [int(w["attack_raw"]) for w in data[:3]]
        self.assertTrue(attacks[0] >= attacks[1] >= attacks[2])

    def test_weapons_detail_endpoint(self):
        weapon = Weapon.objects.get(external_id=900001)
        resp = self.client.get(f"/api/v1/mhw/weapons/{weapon.id}/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["id"], weapon.id)
        self.assertEqual(data["external_id"], 900001)
        self.assertEqual(data["name"], "Test Long Sword A")
        self.assertEqual(data["weapon_type"], "Long Sword")
        self.assertEqual(int(data["rarity"]), 6)


# ==================================================
# Skills API tests (deterministic, no import file required)
# ==================================================
class SkillAPITests(TestCase):
    """
    Skills API tests that do NOT depend on external JSON imports.

    Matches the Weapons test philosophy:
    - deterministic
    - fast
    - validates list/paged/detail + minimal filters
    """

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
        self.assertIsInstance(data["results"], list)
        self.assertLessEqual(len(data["results"]), 2)

    def test_skills_detail_endpoint(self):
        skill = Skill.objects.get(external_id=910001)
        resp = self.client.get(f"/api/v1/mhw/skills/{skill.id}/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["id"], skill.id)
        self.assertEqual(data["external_id"], 910001)
        self.assertEqual(data["name"], "Attack Boost")
        self.assertIn("max_level", data)

    def test_skills_filter_min_level(self):
        resp = self.client.get("/api/v1/mhw/skills/?min_level=7")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)

        for s in data:
            self.assertGreaterEqual(int(s["max_level"]), 7)

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
    Armors API tests that do NOT depend on external JSON imports.

    Validates:
    - list returns array
    - paged returns {count,next,previous,results}
    - detail returns expected fields + nested armor_skills
    - filters: armor_type, rarity range, min_defense, has_skill
    """

    @classmethod
    def setUpTestData(cls):
        # Skills used for ArmorSkill joins
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

        # Armors
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
        )

        # Join rows (armor -> skill with levels)
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

        # List is lightweight: should NOT include nested skills
        self.assertNotIn("armor_skills", first)

    def test_armor_paged_returns_paginated_shape(self):
        resp = self.client.get("/api/v1/mhw/armors/paged/?limit=1&offset=0")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, dict)
        self.assertIn("count", data)
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
        self.assertLessEqual(len(data["results"]), 1)

    def test_armor_detail_includes_nested_skills(self):
        armor = Armor.objects.get(external_id=930002)
        resp = self.client.get(f"/api/v1/mhw/armors/{armor.id}/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["external_id"], 930002)
        self.assertIn("armor_skills", data)
        self.assertIsInstance(data["armor_skills"], list)
        self.assertGreaterEqual(len(data["armor_skills"]), 1)

        first_entry = data["armor_skills"][0]
        self.assertIn("skill", first_entry)
        self.assertIn("level", first_entry)
        self.assertIn("name", first_entry["skill"])

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

    def test_armor_filter_has_skill(self):
        # Should match armors that have "Attack Boost" via join
        resp = self.client.get("/api/v1/mhw/armors/?has_skill=attack")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)

        # Ensure no duplicates due to joins
        ids = [a["id"] for a in data if "id" in a]
        self.assertEqual(len(ids), len(set(ids)))