from __future__ import annotations

import unittest

from prompt_builder.paths import (
    AUTOS_PATH,
    DATA_DIR,
    DOCS_SAMPLES_DIR,
    HOROSCOPE_AUTO_PATH,
    HOROSCOPE_DATE_PATH,
    LINKS_PATH,
    PROJECT_ROOT,
    REPAIR_PROMPTS_PATH,
    TUNING_PROMPTS_PATH,
)


class PathsTests(unittest.TestCase):
    def test_data_files_exist(self) -> None:
        self.assertTrue(DATA_DIR.is_dir())
        for path in (
            AUTOS_PATH,
            REPAIR_PROMPTS_PATH,
            TUNING_PROMPTS_PATH,
            HOROSCOPE_AUTO_PATH,
            HOROSCOPE_DATE_PATH,
            LINKS_PATH,
        ):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), f"missing {path}")

    def test_paths_live_under_project_root(self) -> None:
        self.assertEqual(DATA_DIR.parent, PROJECT_ROOT)
        self.assertTrue(str(AUTOS_PATH).startswith(str(DATA_DIR)))

    def test_docs_samples_dir_exists(self) -> None:
        self.assertTrue(DOCS_SAMPLES_DIR.is_dir())
        self.assertTrue(any(DOCS_SAMPLES_DIR.glob("*.md")))


if __name__ == "__main__":
    unittest.main()
