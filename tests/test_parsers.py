from __future__ import annotations

import unittest
from datetime import date

from prompt_builder.models import Car
from prompt_builder.parsers.autos import load_cars
from prompt_builder.parsers.horoscope import load_horoscope_templates
from prompt_builder.parsers.links import load_links_template
from prompt_builder.parsers.prompts import load_prompt_sections, sections_for_category
from prompt_builder.paths import (
    AUTOS_PATH,
    HOROSCOPE_AUTO_PATH,
    HOROSCOPE_DATE_PATH,
    LINKS_PATH,
    REPAIR_PROMPTS_PATH,
    TUNING_PROMPTS_PATH,
)
from prompt_builder.services.prompt_builder import (
    build_horoscope_auto_prompt,
    build_horoscope_date_prompt,
    build_links_prompt,
    build_prompt,
)


class ParserTests(unittest.TestCase):
    def test_load_cars(self) -> None:
        cars = load_cars(AUTOS_PATH)
        self.assertGreater(len(cars), 0)
        first = cars[0]
        self.assertTrue(first.make)
        self.assertTrue(first.model)
        self.assertIn("·", first.display())

    def test_load_prompt_sections(self) -> None:
        sections = load_prompt_sections(REPAIR_PROMPTS_PATH, TUNING_PROMPTS_PATH)
        repair = sections_for_category(sections, "repair")
        tuning = sections_for_category(sections, "tuning")
        self.assertGreater(len(repair), 0)
        self.assertGreater(len(tuning), 0)
        self.assertIn("[MAKE]", repair[0].template)
        self.assertIn("[MODEL]", tuning[0].template)

    def test_load_horoscope_templates(self) -> None:
        templates = load_horoscope_templates(HOROSCOPE_AUTO_PATH, HOROSCOPE_DATE_PATH)
        self.assertIn("[МАРКА]", templates.auto)
        self.assertIn("[МОДЕЛЬ]", templates.date)
        self.assertIn("[ДАТА_НАЧАЛА]", templates.date)
        self.assertIn("[КОЛИЧЕСТВО_ДНЕЙ]", templates.date)

    def test_load_links_template(self) -> None:
        template = load_links_template(LINKS_PATH)
        self.assertIn("[МАРКА]", template)
        self.assertIn("[МОДЕЛЬ]", template)


class PromptBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.car = Car(make="Chevrolet", model="Tahoe", generation="GMT K2XX", engine="L86")

    def test_build_prompt_replaces_placeholders(self) -> None:
        template = "[MAKE] [MODEL] [GENERATION] [ENGINE]"
        result = build_prompt(template, self.car)
        self.assertEqual(result, "Chevrolet Tahoe GMT K2XX L86")

    def test_horoscope_auto_replaces_russian_placeholders(self) -> None:
        result = build_horoscope_auto_prompt("[МАРКА] / [МОДЕЛЬ]", self.car)
        self.assertEqual(result, "Chevrolet / Tahoe")

    def test_links_replaces_russian_placeholders(self) -> None:
        result = build_links_prompt("[МАРКА] / [МОДЕЛЬ]", self.car)
        self.assertEqual(result, "Chevrolet / Tahoe")

    def test_horoscope_date_replaces_date_and_days(self) -> None:
        result = build_horoscope_date_prompt(
            "[МАРКА] [МОДЕЛЬ] [ДАТА_НАЧАЛА] [КОЛИЧЕСТВО_ДНЕЙ]",
            self.car,
            date(2026, 8, 14),
            7,
        )
        self.assertEqual(result, "Chevrolet Tahoe 2026-08-14 7")


if __name__ == "__main__":
    unittest.main()
