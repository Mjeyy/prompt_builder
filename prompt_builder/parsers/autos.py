from pathlib import Path

from prompt_builder.models import Car


def load_cars(path: Path) -> list[Car]:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    if len(lines) < 2:
        raise ValueError(f"Файл {path.name} не содержит таблицу авто")

    header_line = lines[0].strip()
    if not header_line.startswith("|") or "make" not in header_line.lower():
        raise ValueError(f"Файл {path.name}: ожидается markdown-таблица с колонкой make")

    headers = [cell.strip().lower() for cell in header_line.strip("|").split("|")]
    required = {"make", "model", "generation", "engine"}
    if not required.issubset(headers):
        missing = required - set(headers)
        raise ValueError(f"Файл {path.name}: отсутствуют колонки: {', '.join(sorted(missing))}")

    indices = {name: headers.index(name) for name in required}
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

    if not cars:
        raise ValueError(f"Файл {path.name} не содержит данных об авто")

    return cars
