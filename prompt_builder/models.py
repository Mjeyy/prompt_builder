from dataclasses import dataclass
from datetime import date
from typing import Literal

Category = Literal["repair", "tuning"]
WorkMode = Literal["repair", "tuning", "horoscope_auto", "horoscope_date"]
HoroscopeMode = Literal["auto", "date"]

CATEGORY_LABELS: dict[Category, str] = {
    "repair": "Ремонт",
    "tuning": "Тюнинг",
}

WORK_MODE_LABELS: dict[WorkMode, str] = {
    "repair": "Ремонт",
    "tuning": "Тюнинг",
    "horoscope_auto": "Гороскоп: описание авто",
    "horoscope_date": "Гороскоп: прогноз",
}

BUILDER_LABEL = "Сборка промпта"
TABLE_QA_LABEL = "Проверка таблиц"
HOME_LABEL = "Главная"


@dataclass(frozen=True)
class Car:
    make: str
    model: str
    generation: str
    engine: str

    def display(self) -> str:
        return f"{self.make} {self.model} · {self.generation} · {self.engine}"

    def display_short(self) -> str:
        return f"{self.make} {self.model}"


@dataclass(frozen=True)
class PromptSection:
    id: str
    title: str
    template: str
    category: Category

    def display(self) -> str:
        return f"{self.id} — {self.title}"


@dataclass
class Selection:
    car: Car
    section: PromptSection

    @property
    def category_label(self) -> str:
        return CATEGORY_LABELS[self.section.category]


@dataclass(frozen=True)
class HoroscopeTemplates:
    auto: str
    date: str


@dataclass(frozen=True)
class HoroscopeForecastSelection:
    car: Car
    start_date: date
    days: int
