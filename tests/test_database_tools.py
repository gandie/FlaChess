from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


class DatabaseToolTests(unittest.TestCase):
    def test_seed_script_adds_random_players_and_draft_tournaments(self) -> None:
        script = (TOOLS / "seed_database.sql").read_text(encoding="utf-8")

        self.assertIn("INSERT INTO player (name)", script)
        self.assertIn("INSERT INTO tournament", script)
        self.assertIn("'draft'", script)
        self.assertGreaterEqual(script.count("ORDER BY random()"), 2)
        self.assertTrue(script.strip().endswith("COMMIT;"))

    def test_cleanup_script_truncates_roots_and_resets_all_identities(self) -> None:
        script = (TOOLS / "cleanup_database.sql").read_text(encoding="utf-8")

        truncate = re.search(
            r"TRUNCATE TABLE tournament,\s*player "
            r"RESTART IDENTITY CASCADE;",
            script,
        )
        self.assertIsNotNone(truncate)

    def test_psql_helper_supports_inline_queries_and_sql_files(self) -> None:
        helper = (TOOLS / "psql.ps1").read_text(encoding="utf-8")

        self.assertIn('ParameterSetName = "Query"', helper)
        self.assertIn('ParameterSetName = "File"', helper)
        self.assertIn("Get-Content -LiteralPath $File -Raw", helper)
        self.assertIn('"-c", $Query', helper)


if __name__ == "__main__":
    unittest.main()
