from enum import Enum
from typing import TypeVar

import questionary
from questionary import Choice

from prompt_builder.models import CATEGORY_LABELS, Car, Category, PromptSection, Selection
from prompt_builder.parsers.prompts import sections_for_category
from prompt_builder.services.clipboard import ClipboardError, copy_to_clipboard
from prompt_builder.services.prompt_builder import build_prompt

T = TypeVar("T")


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


def select_category() -> Category | None:
    choices = [
        Choice(title=CATEGORY_LABELS["repair"], value="repair"),
        Choice(title=CATEGORY_LABELS["tuning"], value="tuning"),
    ]
    return _select("Категория:", choices)


def select_section(sections: list[PromptSection], category: Category) -> PromptSection | None:
    category_sections = sections_for_category(sections, category)
    choices = [Choice(title=section.display(), value=section) for section in category_sections]
    return _select("Раздел:", choices)


def select_post_action() -> PostAction | None:
    choices = [
        Choice(title=POST_ACTION_LABELS[action], value=action) for action in PostAction
    ]
    return _select("Что дальше?", choices)


def copy_and_report(selection: Selection, prompt_text: str) -> bool:
    try:
        copy_to_clipboard(prompt_text)
    except ClipboardError as exc:
        print(f"\n✗ Не удалось скопировать в буфер обмена: {exc}\n")
        return False

    print("\n✓ Промпт скопирован в буфер обмена\n")
    print(f"  Авто:       {selection.car.display()}")
    print(f"  Категория:  {selection.category_label}")
    print(f"  Раздел:     {selection.section.display()}\n")
    return True


def build_selection_prompt(selection: Selection) -> str:
    return build_prompt(selection.section.template, selection.car)
