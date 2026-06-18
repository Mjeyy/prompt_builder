import re
from pathlib import Path

from prompt_builder.models import Category, PromptSection

REPAIR_HEADER = re.compile(
    r"^###\s+\d+\.\s+(\w+)\s+—\s+(.+?)\s+\(Repair\)\s*$",
    re.MULTILINE,
)
TUNING_HEADER = re.compile(
    r"^##\s+\d+\.\s+(\w+)\s+—\s+(.+?)\s*$",
    re.MULTILINE,
)
TEXT_BLOCK = re.compile(r"```text\n(.*?)```", re.DOTALL)


def _parse_sections(content: str, category: Category, header_pattern: re.Pattern[str]) -> list[PromptSection]:
    sections: list[PromptSection] = []
    headers = list(header_pattern.finditer(content))

    if not headers:
        raise ValueError(f"Не найдено ни одного раздела промптов (категория: {category})")

    for index, match in enumerate(headers):
        section_id = match.group(1)
        title = match.group(2).strip()
        start = match.end()
        end = headers[index + 1].start() if index + 1 < len(headers) else len(content)
        block_match = TEXT_BLOCK.search(content, start, end)

        if not block_match:
            raise ValueError(
                f"Раздел {section_id} ({category}): не найден блок ```text после заголовка"
            )

        sections.append(
            PromptSection(
                id=section_id,
                title=title,
                template=block_match.group(1),
                category=category,
            )
        )

    return sections


def load_prompt_sections(repair_path: Path, tuning_path: Path) -> list[PromptSection]:
    repair_content = repair_path.read_text(encoding="utf-8")
    tuning_content = tuning_path.read_text(encoding="utf-8")

    sections = _parse_sections(repair_content, "repair", REPAIR_HEADER)
    sections.extend(_parse_sections(tuning_content, "tuning", TUNING_HEADER))
    return sections


def sections_for_category(sections: list[PromptSection], category: Category) -> list[PromptSection]:
    return [section for section in sections if section.category == category]
