from pathlib import Path

from prompt_builder.models import HoroscopeTemplates


def load_horoscope_templates(auto_path: Path, date_path: Path) -> HoroscopeTemplates:
    auto_text = auto_path.read_text(encoding="utf-8")
    date_text = date_path.read_text(encoding="utf-8")

    if not auto_text.strip():
        raise ValueError(f"Файл {auto_path.name} пуст")
    if not date_text.strip():
        raise ValueError(f"Файл {date_path.name} пуст")

    return HoroscopeTemplates(auto=auto_text, date=date_text)
