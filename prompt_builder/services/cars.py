from prompt_builder.models import Car


def visible_cars(cars: list[Car], hidden: set[Car]) -> list[Car]:
    return [car for car in cars if car not in hidden]


def unique_make_model_cars(cars: list[Car]) -> list[Car]:
    seen: set[tuple[str, str]] = set()
    unique: list[Car] = []
    for car in cars:
        key = (car.make, car.model)
        if key in seen:
            continue
        seen.add(key)
        unique.append(car)
    return unique


def sorted_cars(cars: list[Car], *, alphabetical: bool) -> list[Car]:
    if not alphabetical:
        return list(cars)
    return sorted(
        cars,
        key=lambda car: (
            car.make.casefold(),
            car.model.casefold(),
            car.generation.casefold(),
            car.engine.casefold(),
        ),
    )
