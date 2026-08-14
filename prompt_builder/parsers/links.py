from pathlib import Path


def load_links_template(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Файл {path.name} пуст")
    return text
