from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from prompt_builder.models import Car
from prompt_builder.parsers.autos import load_cars, load_hidden_cars, save_hidden_cars
from prompt_builder.paths import AUTOS_HIDDEN_PATH, AUTOS_PATH
from prompt_builder.services.cars import sorted_cars, unique_make_model_cars, visible_cars


def _car(make: str, model: str, generation: str = "G", engine: str = "E") -> Car:
    return Car(make=make, model=model, generation=generation, engine=engine)


class HiddenCarsParserTests(unittest.TestCase):
    def test_committed_sidecar_is_empty(self) -> None:
        hidden = load_hidden_cars(AUTOS_HIDDEN_PATH)
        self.assertEqual(hidden, set())

    def test_missing_file_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing_autos_hidden.md"
            self.assertEqual(load_hidden_cars(missing), set())

    def test_empty_table_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autos_hidden.md"
            path.write_text(
                "| make | model | generation | engine |\n"
                "|------|-------|------------|--------|\n",
                encoding="utf-8",
            )
            self.assertEqual(load_hidden_cars(path), set())

    def test_save_load_roundtrip_follows_catalog_order(self) -> None:
        catalog = [
            _car("Chevrolet", "Tahoe", "K2", "L86"),
            _car("GMC", "Yukon", "K2", "L86"),
            _car("Jeep", "Wrangler", "JK", "V6"),
        ]
        hidden = {catalog[2], catalog[0]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autos_hidden.md"
            save_hidden_cars(path, hidden, catalog)
            loaded = load_hidden_cars(path)
            text = path.read_text(encoding="utf-8")
        self.assertEqual(loaded, hidden)
        tahoe_at = text.index("Tahoe")
        wrangler_at = text.index("Wrangler")
        self.assertLess(tahoe_at, wrangler_at)
        self.assertNotIn("Yukon", text)


class CarListServiceTests(unittest.TestCase):
    def test_visible_cars_keeps_file_order(self) -> None:
        catalog = [
            _car("Chevrolet", "Tahoe"),
            _car("GMC", "Yukon"),
            _car("Jeep", "Wrangler"),
        ]
        hidden = {catalog[1]}
        visible = visible_cars(catalog, hidden)
        self.assertEqual(visible, [catalog[0], catalog[2]])

    def test_orphan_hidden_entry_does_not_change_catalog(self) -> None:
        catalog = [_car("Chevrolet", "Tahoe")]
        orphan = _car("Ford", "Focus")
        self.assertEqual(visible_cars(catalog, {orphan}), catalog)

    def test_unique_make_model_keeps_first_occurrence(self) -> None:
        first = _car("Mercedes-Benz", "SL-Class", "R231", "V6")
        second = _car("Mercedes-Benz", "SL-Class", "R231", "V8")
        other = _car("Jeep", "Wrangler", "JK", "V6")
        unique = unique_make_model_cars([first, second, other])
        self.assertEqual(unique, [first, other])

    def test_unique_make_model_on_catalog(self) -> None:
        cars = load_cars(AUTOS_PATH)
        unique = unique_make_model_cars(cars)
        self.assertLess(len(unique), len(cars))
        keys = [(car.make, car.model) for car in unique]
        self.assertEqual(len(keys), len(set(keys)))
        first_sl = next(car for car in cars if car.make == "Mercedes-Benz" and car.model == "SL-Class")
        self.assertIn(first_sl, unique)

    def test_sorted_cars_file_order_is_a_copy(self) -> None:
        catalog = [_car("GMC", "Yukon"), _car("Chevrolet", "Tahoe")]
        result = sorted_cars(catalog, alphabetical=False)
        self.assertEqual(result, catalog)
        result.append(_car("Jeep", "Wrangler"))
        self.assertEqual(len(catalog), 2)

    def test_sorted_cars_alphabetical_by_make_then_model(self) -> None:
        camaro = _car("Chevrolet", "Camaro")
        tahoe = _car("Chevrolet", "Tahoe")
        yukon = _car("GMC", "Yukon")
        catalog = [yukon, tahoe, camaro]
        result = sorted_cars(catalog, alphabetical=True)
        self.assertEqual(result, [camaro, tahoe, yukon])


if __name__ == "__main__":
    unittest.main()
