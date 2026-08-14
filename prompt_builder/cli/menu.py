from datetime import date, timedelta
from enum import Enum
from typing import TypeVar

import questionary
from questionary import Choice

from prompt_builder.models import (
    WORK_MODE_LABELS,
    Car,
    Category,
    HoroscopeForecastSelection,
    PromptSection,
    Selection,
    WorkMode,
)
from prompt_builder.parsers.prompts import sections_for_category
from prompt_builder.services.clipboard import ClipboardError, copy_to_clipboard
from prompt_builder.services.prompt_builder import build_prompt

T = TypeVar("T")

_MANUAL = "__manual__"
DATE_FORMAT_HINT = "ГГГГ-ММ-ДД"
NEARBY_DATE_COUNT = 14


class PostAction(str, Enum):
    REPEAT = "repeat"
    OTHER_SECTION = "other_section"
    OTHER_CATEGORY = "other_category"
    CHANGE_CAR = "change_car"
    EXIT = "exit"


POST_ACTION_LABELS = {
    PostAction.REPEAT: "Повторить",
    PostAction.OTHER_SECTION: "Другой раздел",
    PostAction.OTHER_CATEGORY: "Другая категория",
    PostAction.CHANGE_CAR: "Сменить авто",
    PostAction.EXIT: "Выход",
}


def _select(title: str, choices: list[Choice]) -> T | None:
    return questionary.select(title, choices=choices).ask()


def select_car(cars: list[Car]) -> Car | None:
    choices = [Choice(title=car.display(), value=car) for car in cars]
    return _select("Выберите авто:", choices)


def select_category() -> WorkMode | None:
    choices = [
        Choice(title=WORK_MODE_LABELS[mode], value=mode)
        for mode in ("repair", "tuning", "links", "horoscope_auto", "horoscope_date")
    ]
    return _select("Категория:", choices)


def select_section(sections: list[PromptSection], category: Category) -> PromptSection | None:
    category_sections = sections_for_category(sections, category)
    choices = [Choice(title=section.display(), value=section) for section in category_sections]
    return _select("Раздел:", choices)


def select_start_date() -> date | None:
    today = date.today()
    choices: list[Choice] = []
    for offset in range(NEARBY_DATE_COUNT):
        day = today + timedelta(days=offset)
        iso = day.isoformat()
        if offset == 0:
            title = f"Сегодня ({iso})"
        elif offset == 1:
            title = f"Завтра ({iso})"
        else:
            title = iso
        choices.append(Choice(title=title, value=day))
    choices.append(Choice(title="Ввести вручную", value=_MANUAL))

    selected = _select("Дата начала прогноза:", choices)
    if selected is None:
        return None
    if selected == _MANUAL:
        return _ask_manual_date()
    return selected


def _ask_manual_date() -> date | None:
    while True:
        raw = questionary.text(
            f"Введите дату в формате {DATE_FORMAT_HINT} (например, {date.today().isoformat()}):"
        ).ask()
        if raw is None:
            return None
        raw = raw.strip()
        try:
            return date.fromisoformat(raw)
        except ValueError:
            print(f"Неверный формат. Нужна дата вида {DATE_FORMAT_HINT}, например {date.today().isoformat()}.")


def select_forecast_days() -> int | None:
    choices = [
        Choice(title="7 дней", value=7),
        Choice(title="10 дней", value=10),
        Choice(title="30 дней", value=30),
        Choice(title="Указать вручную", value=_MANUAL),
    ]
    selected = _select("Количество дней:", choices)
    if selected is None:
        return None
    if selected == _MANUAL:
        return _ask_manual_days()
    return selected


def _ask_manual_days() -> int | None:
    while True:
        raw = questionary.text("Введите количество дней (целое число ≥ 1):").ask()
        if raw is None:
            return None
        try:
            days = int(raw.strip())
        except ValueError:
            print("Нужно целое число не меньше 1.")
            continue
        if days >= 1:
            return days
        print("Нужно целое число не меньше 1.")


def select_post_action(*, include_other_section: bool = True) -> PostAction | None:
    actions = [PostAction.REPEAT]
    if include_other_section:
        actions.append(PostAction.OTHER_SECTION)
    actions.extend([PostAction.OTHER_CATEGORY, PostAction.CHANGE_CAR, PostAction.EXIT])
    choices = [Choice(title=POST_ACTION_LABELS[action], value=action) for action in actions]
    return _select("Что дальше?", choices)


def _copy_or_fail(prompt_text: str) -> bool:
    try:
        copy_to_clipboard(prompt_text)
    except ClipboardError as exc:
        print(f"\n✗ Не удалось скопировать в буфер обмена: {exc}\n")
        return False
    print("\n✓ Промпт скопирован в буфер обмена\n")
    return True


def copy_and_report(selection: Selection, prompt_text: str) -> bool:
    if not _copy_or_fail(prompt_text):
        return False
    print(f"  Авто:       {selection.car.display()}")
    print(f"  Категория:  {selection.category_label}")
    print(f"  Раздел:     {selection.section.display()}\n")
    return True


def copy_and_report_horoscope_auto(car: Car, prompt_text: str) -> bool:
    if not _copy_or_fail(prompt_text):
        return False
    print(f"  Авто:       {car.display_short()}")
    print(f"  Категория:  {WORK_MODE_LABELS['horoscope_auto']}\n")
    return True


def copy_and_report_links(car: Car, prompt_text: str) -> bool:
    if not _copy_or_fail(prompt_text):
        return False
    print(f"  Авто:       {car.display_short()}")
    print(f"  Категория:  {WORK_MODE_LABELS['links']}\n")
    return True


def copy_and_report_horoscope_date(
    selection: HoroscopeForecastSelection,
    prompt_text: str,
) -> bool:
    if not _copy_or_fail(prompt_text):
        return False
    print(f"  Авто:       {selection.car.display_short()}")
    print(f"  Категория:  {WORK_MODE_LABELS['horoscope_date']}")
    print(f"  Дата:       {selection.start_date.isoformat()}")
    print(f"  Дней:       {selection.days}\n")
    return True


def build_selection_prompt(selection: Selection) -> str:
    return build_prompt(selection.section.template, selection.car)
