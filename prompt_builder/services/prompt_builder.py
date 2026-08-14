from datetime import date

from prompt_builder.models import Car


def build_prompt(template: str, car: Car) -> str:
    return (
        template.replace("[MAKE]", car.make)
        .replace("[MODEL]", car.model)
        .replace("[GENERATION]", car.generation)
        .replace("[ENGINE]", car.engine)
    )


def _replace_car_ru(template: str, car: Car) -> str:
    return template.replace("[МАРКА]", car.make).replace("[МОДЕЛЬ]", car.model)


def build_horoscope_auto_prompt(template: str, car: Car) -> str:
    return _replace_car_ru(template, car)


def build_horoscope_date_prompt(template: str, car: Car, start_date: date, days: int) -> str:
    return (
        _replace_car_ru(template, car)
        .replace("[ДАТА_НАЧАЛА]", start_date.isoformat())
        .replace("[КОЛИЧЕСТВО_ДНЕЙ]", str(days))
    )
