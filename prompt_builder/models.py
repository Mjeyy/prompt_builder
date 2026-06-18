from dataclasses import dataclass
from typing import Literal

Category = Literal["repair", "tuning"]

CATEGORY_LABELS: dict[Category, str] = {
    "repair": "Ремонт",
    "tuning": "Тюнинг",
}


@dataclass(frozen=True)
class Car:
    make: str
    model: str
    generation: str
    engine: str

    def display(self) -> str:
        return f"{self.make} {self.model} · {self.generation} · {self.engine}"


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
