from prompt_builder.models import Car


def build_prompt(template: str, car: Car) -> str:
    return (
        template.replace("[MAKE]", car.make)
        .replace("[MODEL]", car.model)
        .replace("[GENERATION]", car.generation)
        .replace("[ENGINE]", car.engine)
    )
