import sys
from pathlib import Path

from prompt_builder.models import Car, PromptSection, Selection
from prompt_builder.parsers.autos import load_cars
from prompt_builder.parsers.prompts import load_prompt_sections
from prompt_builder.ui.menu import (
    PostAction,
    build_selection_prompt,
    copy_and_report,
    select_car,
    select_category,
    select_post_action,
    select_section,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_data() -> tuple[list[Car], list[PromptSection]]:
    autos_path = PROJECT_ROOT / "autos.md"
    repair_path = PROJECT_ROOT / "repair_prompts.md"
    tuning_path = PROJECT_ROOT / "tuning_prompts.md"

    cars = load_cars(autos_path)
    sections = load_prompt_sections(repair_path, tuning_path)
    return cars, sections


def run() -> None:
    try:
        cars, sections = _load_data()
    except (OSError, ValueError) as exc:
        print(f"Ошибка загрузки данных: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    car: Car | None = None
    category = None
    selection: Selection | None = None
    prompt_text = ""

    while True:
        if car is None:
            car = select_car(cars)
            if car is None:
                break
            category = None
            selection = None

        if category is None:
            category = select_category()
            if category is None:
                car = None
                continue

        if selection is None or selection.section.category != category or selection.car != car:
            section = select_section(sections, category)
            if section is None:
                category = None
                continue
            selection = Selection(car=car, section=section)
            prompt_text = build_selection_prompt(selection)

        if not copy_and_report(selection, prompt_text):
            continue

        action = select_post_action()
        if action is None or action == PostAction.EXIT:
            break
        if action == PostAction.REPEAT:
            continue
        if action == PostAction.OTHER_SECTION:
            selection = None
            continue
        if action == PostAction.OTHER_CATEGORY:
            category = None
            selection = None
            continue
        if action == PostAction.CHANGE_CAR:
            car = None
            category = None
            selection = None


def main() -> None:
    try:
        run()
    except KeyboardInterrupt:
        print("\nЗавершено.")
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
