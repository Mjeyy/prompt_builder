import sys
from pathlib import Path

from prompt_builder.models import (
    Car,
    Category,
    HoroscopeForecastSelection,
    HoroscopeTemplates,
    PromptSection,
    Selection,
    WorkMode,
)
from prompt_builder.parsers.autos import load_cars
from prompt_builder.parsers.horoscope import load_horoscope_templates
from prompt_builder.parsers.prompts import load_prompt_sections
from prompt_builder.services.prompt_builder import (
    build_horoscope_auto_prompt,
    build_horoscope_date_prompt,
)
from prompt_builder.ui.menu import (
    PostAction,
    build_selection_prompt,
    copy_and_report,
    copy_and_report_horoscope_auto,
    copy_and_report_horoscope_date,
    select_car,
    select_category,
    select_forecast_days,
    select_post_action,
    select_section,
    select_start_date,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_data() -> tuple[list[Car], list[PromptSection], HoroscopeTemplates]:
    cars = load_cars(PROJECT_ROOT / "autos.md")
    sections = load_prompt_sections(
        PROJECT_ROOT / "repair_prompts.md",
        PROJECT_ROOT / "tuning_prompts.md",
    )
    templates = load_horoscope_templates(
        PROJECT_ROOT / "horoscop_auto.md",
        PROJECT_ROOT / "horoscop_date.md",
    )
    return cars, sections, templates


def _reset_work() -> tuple[None, None, None, str]:
    return None, None, None, ""


def run() -> None:
    try:
        cars, sections, horoscope = _load_data()
    except (OSError, ValueError) as exc:
        print(f"Ошибка загрузки данных: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    car: Car | None = None
    mode: WorkMode | None = None
    selection: Selection | None = None
    forecast: HoroscopeForecastSelection | None = None
    prompt_text = ""

    while True:
        if car is None:
            car = select_car(cars)
            if car is None:
                break
            mode, selection, forecast, prompt_text = _reset_work()

        if mode is None:
            mode = select_category()
            if mode is None:
                car = None
                continue
            selection = None
            forecast = None
            prompt_text = ""

        if mode in ("repair", "tuning"):
            category: Category = mode
            if selection is None or selection.section.category != category or selection.car != car:
                section = select_section(sections, category)
                if section is None:
                    mode = None
                    continue
                selection = Selection(car=car, section=section)
                prompt_text = build_selection_prompt(selection)

            if not copy_and_report(selection, prompt_text):
                continue
            action = select_post_action(include_other_section=True)

        elif mode == "horoscope_auto":
            prompt_text = build_horoscope_auto_prompt(horoscope.auto, car)
            if not copy_and_report_horoscope_auto(car, prompt_text):
                continue
            action = select_post_action(include_other_section=False)

        else:
            if forecast is None:
                start = select_start_date()
                if start is None:
                    mode = None
                    continue
                days = select_forecast_days()
                if days is None:
                    mode = None
                    continue
                forecast = HoroscopeForecastSelection(car=car, start_date=start, days=days)
                prompt_text = build_horoscope_date_prompt(
                    horoscope.date, car, start, days
                )

            if not copy_and_report_horoscope_date(forecast, prompt_text):
                continue
            action = select_post_action(include_other_section=False)

        if action is None or action == PostAction.EXIT:
            break
        if action == PostAction.REPEAT:
            continue
        if action == PostAction.OTHER_SECTION:
            selection = None
            continue
        if action == PostAction.OTHER_CATEGORY:
            mode = None
            selection = None
            forecast = None
            prompt_text = ""
            continue
        if action == PostAction.CHANGE_CAR:
            car = None
            mode, selection, forecast, prompt_text = _reset_work()


def main() -> None:
    try:
        run()
    except KeyboardInterrupt:
        print("\nЗавершено.")
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
