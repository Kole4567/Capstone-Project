from pathlib import Path

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Monster, MonsterWeakness


class MHWImportAndAPITests(TestCase):
    """
    Minimal regression tests for:
    - import pipeline (basic sanity)
    - core API endpoints (status + basic response shape)
    - a few filter queries

    Notes
    - These tests use the repository-tracked JSON file: data/mhw_monsters.json
    - We keep tests intentionally lightweight (no pytest required).
    """

    @classmethod
    def setUpTestData(cls):
        """
        Import test data once for this TestCase class.

        This is faster than importing in setUp() for every single test method.
        """
        # Build an absolute path to the repo-tracked JSON file.
        # manage.py is run from the project root (mysite/), so BASE_DIR is one level up.
        base_dir = Path(__file__).resolve().parent.parent  # .../mysite/
        json_path = base_dir / "data" / "mhw_monsters.json"

        # Sanity check: fail early if the file is missing.
        if not json_path.exists():
            raise FileNotFoundError(f"Missing test data file: {json_path}")

        # Run import with reset to ensure a clean state.
        call_command(
            "import_mhw",
            monsters=str(json_path),
            reset=True,
        )

    def setUp(self):
        self.client = APIClient()

    # ------------------------------------------------------------
    # Import sanity
    # ------------------------------------------------------------
    def test_import_populates_monsters(self):
        """
        Basic sanity: database should have monsters after import.
        """
        self.assertGreater(Monster.objects.count(), 0)

    def test_import_populates_weaknesses(self):
        """
        Basic sanity: weaknesses should exist after import.
        """
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

        # Check a few expected fields on the first item
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

        # Detail should include weaknesses (based on your serializer contract)
        self.assertIn("weaknesses", data)
        self.assertIsInstance(data["weaknesses"], list)

    # ------------------------------------------------------------
    # Filters (minimal set)
    # ------------------------------------------------------------
    def test_filter_is_elder_dragon(self):
        resp = self.client.get("/api/v1/mhw/monsters/?is_elder_dragon=true")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)

        # If any returned, they should all be elder dragons
        for m in data:
            self.assertTrue(m.get("is_elder_dragon"))

    def test_filter_element_and_min_stars(self):
        # Fire is commonly present; min_stars within valid range.
        resp = self.client.get("/api/v1/mhw/monsters/?element=Fire&min_stars=2")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIsInstance(data, list)

        # Optional strictness: ensure no duplicate monster IDs due to joins.
        ids = [m["id"] for m in data if "id" in m]
        self.assertEqual(len(ids), len(set(ids)))

    def test_invalid_min_stars_is_ignored(self):
        # Out-of-range should be ignored (should not 500)
        resp = self.client.get("/api/v1/mhw/monsters/?element=Fire&min_stars=999")
        self.assertEqual(resp.status_code, 200)