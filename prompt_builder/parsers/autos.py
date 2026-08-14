from pathlib import Path

from prompt_builder.models import Car

_REQUIRED = ("make", "model", "generation", "engine")
_HIDDEN_HEADER = "| make | model | generation | engine |"
_HIDDEN_SEPARATOR = "|------|-------|------------|--------|"


def load_cars(path: Path) -> list[Car]:
    return _read_car_rows(path, allow_missing=False, allow_empty=False)


def load_hidden_cars(path: Path) -> set[Car]:
    return set(_read_car_rows(path, allow_missing=True, allow_empty=True))


def save_hidden_cars(path: Path, hidden: set[Car], catalog: list[Car]) -> None:
    ordered = [car for car in catalog if car in hidden]
    lines = [_HIDDEN_HEADER, _HIDDEN_SEPARATOR]
    for car in ordered:
        lines.append(f"| {car.make} | {car.model} | {car.generation} | {car.engine} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_car_rows(path: Path, *, allow_missing: bool, allow_empty: bool) -> list[Car]:
    if allow_missing and not path.exists():
        return []

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        if allow_empty:
            return []
        raise ValueError(f"Файл {path.name} не содержит таблицу авто")

    lines = text.splitlines()
    if len(lines) < 2:
        if allow_empty:
            return []
        raise ValueError(f"Файл {path.name} не содержит таблицу авто")

    header_line = lines[0].strip()
    if not header_line.startswith("|") or "make" not in header_line.lower():
        raise ValueError(f"Файл {path.name}: ожидается markdown-таблица с колонкой make")

    headers = [cell.strip().lower() for cell in header_line.strip("|").split("|")]
    required = set(_REQUIRED)
    if not required.issubset(headers):
        missing = required - set(headers)
        raise ValueError(f"Файл {path.name}: отсутствуют колонки: {', '.join(sorted(missing))}")

    indices = {name: headers.index(name) for name in _REQUIRED}
    cars: list[Car] = []

    for line_no, line in enumerate(lines[2:], start=3):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").replace("-", "").strip()) <= {""}:
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < len(headers):
            raise ValueError(f"Файл {path.name}, строка {line_no}: неполная строка таблицы")

        cars.append(
            Car(
                make=cells[indices["make"]],
                model=cells[indices["model"]],
                generation=cells[indices["generation"]],
                engine=cells[indices["engine"]],
            )
        )

    if not cars and not allow_empty:
        raise ValueError(f"Файл {path.name} не содержит данных об авто")

    return cars
