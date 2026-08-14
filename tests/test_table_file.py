from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from prompt_builder.services.table_file import (
    EXPECTED_PARAGRAPHS,
    editor_to_summary,
    find_summary_errors,
    fixed_copy_path,
    load_table,
    paragraph_count,
    summary_to_editor,
)


class SummaryHelpersTests(unittest.TestCase):
    def test_paragraph_count(self) -> None:
        summary = "a<br><br>b<br><br>c<br><br>d"
        self.assertEqual(paragraph_count(summary), EXPECTED_PARAGRAPHS)

    def test_editor_roundtrip(self) -> None:
        summary = "первый<br><br>второй<br><br>третий<br><br>четвёртый"
        editor = summary_to_editor(summary)
        self.assertIn("\n\n", editor)
        self.assertEqual(editor_to_summary(editor), summary)

    def test_fixed_copy_path(self) -> None:
        source = Path("/tmp/article.md")
        self.assertEqual(fixed_copy_path(source).name, "article_fix.md")
        already = Path("/tmp/article_fix.md")
        self.assertEqual(fixed_copy_path(already).name, "article_fix.md")


class TableLoadTests(unittest.TestCase):
    def test_finds_summary_errors(self) -> None:
        content = (
            "| make | model | topic_title | summary |\n"
            "|------|-------|-------------|---------|\n"
            "| Ford | Focus | Ok | a<br><br>b<br><br>c<br><br>d |\n"
            "| Kia | Rio | Bad | only one paragraph |\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as handle:
            handle.write(content)
            path = Path(handle.name)
        try:
            table = load_table(path)
            errors = find_summary_errors(table)
            self.assertEqual(len(table.rows), 2)
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0].topic_title, "Bad")
            self.assertEqual(errors[0].paragraph_count, 1)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
