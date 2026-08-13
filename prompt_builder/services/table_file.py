from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

EXPECTED_PARAGRAPHS = 4
PARAGRAPH_SEPARATOR = "<br><br>"
FIX_SUFFIX = "_fix"


def fixed_copy_path(path: Path) -> Path:
    if path.stem.endswith(FIX_SUFFIX):
        return path
    return path.with_stem(f"{path.stem}{FIX_SUFFIX}")


@dataclass
class TableRow:
    line_no: int
    cells: list[str]
    raw_line: str


@dataclass
class MarkdownTable:
    path: Path
    headers: list[str]
    header_line: str
    separator_line: str
    rows: list[TableRow]
    newline: str = "\n"
    trailing_newline: bool = True
    leading_lines: list[str] = field(default_factory=list)
    trailing_lines: list[str] = field(default_factory=list)
    summary_idx: int = -1
    topic_title_idx: int = -1
    make_idx: int = -1
    model_idx: int = -1

    def cell(self, row: TableRow, index: int, default: str = "") -> str:
        if index < 0 or index >= len(row.cells):
            return default
        return row.cells[index]


@dataclass(frozen=True)
class SummaryError:
    row_index: int
    line_no: int
    topic_title: str
    car_label: str
    summary: str
    paragraph_count: int


def paragraph_count(summary: str) -> int:
    return len(summary.split(PARAGRAPH_SEPARATOR))


def summary_to_editor(summary: str) -> str:
    return summary.replace(PARAGRAPH_SEPARATOR, "\n\n")


def editor_to_summary(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalized.endswith("\n") and not normalized.endswith("\n\n"):
        normalized = normalized[:-1]
    parts = normalized.split("\n\n")
    cleaned = [" ".join(part.split()) for part in parts]
    return PARAGRAPH_SEPARATOR.join(cleaned)


def _split_row(line: str) -> list[str]:
    stripped = line.strip()
    inner = stripped[1:] if stripped.startswith("|") else stripped
    if inner.endswith("|"):
        inner = inner[:-1]
    return inner.split("|")


def _is_separator_line(line: str) -> bool:
    stripped = line.strip().replace("|", "").replace("-", "").replace(":", "").replace(" ", "")
    return line.strip().startswith("|") and stripped == ""


def _header_index(headers: list[str], name: str) -> int:
    lowered = [item.strip().lower() for item in headers]
    try:
        return lowered.index(name)
    except ValueError:
        return -1


def load_table(path: Path) -> MarkdownTable:
    raw = path.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.splitlines()
    if not lines:
        raise ValueError(f"Файл {path.name} пуст")

    header_idx = None
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip().lower() for cell in _split_row(line)]
        if "summary" in cells:
            header_idx = index
            break

    if header_idx is None:
        raise ValueError(f"Файл {path.name}: не найдена markdown-таблица с колонкой summary")

    header_line = lines[header_idx]
    headers = [cell.strip() for cell in _split_row(header_line)]
    summary_idx = _header_index(headers, "summary")
    if summary_idx < 0:
        raise ValueError(f"Файл {path.name}: отсутствует колонка summary")

    separator_idx = header_idx + 1
    if separator_idx >= len(lines) or not _is_separator_line(lines[separator_idx]):
        raise ValueError(f"Файл {path.name}: после заголовка ожидается строка-разделитель таблицы")

    rows: list[TableRow] = []
    trailing_start = None
    for line_no, line in enumerate(lines[separator_idx + 1 :], start=separator_idx + 2):
        stripped = line.strip()
        if not stripped:
            trailing_start = line_no - 1
            break
        if not stripped.startswith("|"):
            trailing_start = line_no - 1
            break
        if _is_separator_line(stripped):
            continue
        rows.append(
            TableRow(
                line_no=line_no,
                cells=_split_row(line),
                raw_line=stripped,
            )
        )

    if not rows:
        raise ValueError(f"Файл {path.name} не содержит строк таблицы")

    trailing_lines: list[str] = []
    if trailing_start is not None:
        trailing_lines = lines[trailing_start:]

    return MarkdownTable(
        path=path,
        headers=headers,
        header_line=header_line.strip(),
        separator_line=lines[separator_idx].strip(),
        rows=rows,
        newline=newline,
        trailing_newline=raw.endswith(("\n", "\r\n")),
        leading_lines=lines[:header_idx],
        trailing_lines=trailing_lines,
        summary_idx=summary_idx,
        topic_title_idx=_header_index(headers, "topic_title"),
        make_idx=_header_index(headers, "make"),
        model_idx=_header_index(headers, "model"),
    )


def find_summary_errors(table: MarkdownTable) -> list[SummaryError]:
    errors: list[SummaryError] = []
    for row_index, row in enumerate(table.rows):
        summary = table.cell(row, table.summary_idx)
        if table.summary_idx >= len(row.cells):
            count = 0
            summary = ""
        else:
            count = paragraph_count(summary)
        if count == EXPECTED_PARAGRAPHS:
            continue

        make = table.cell(row, table.make_idx).strip()
        model = table.cell(row, table.model_idx).strip()
        car_label = " ".join(part for part in (make, model) if part) or "—"
        topic_title = table.cell(row, table.topic_title_idx).strip() or "без названия"
        errors.append(
            SummaryError(
                row_index=row_index,
                line_no=row.line_no,
                topic_title=topic_title,
                car_label=car_label,
                summary=summary,
                paragraph_count=count,
            )
        )
    return errors


def row_summary(table: MarkdownTable, row_index: int) -> str:
    row = table.rows[row_index]
    return table.cell(row, table.summary_idx)


def set_row_summary(table: MarkdownTable, row_index: int, summary: str) -> None:
    row = table.rows[row_index]
    if table.summary_idx >= len(row.cells):
        row.cells.extend([""] * (table.summary_idx - len(row.cells) + 1))
    row.cells[table.summary_idx] = summary
    row.raw_line = "|" + "|".join(row.cells) + "|"


def render_table(table: MarkdownTable) -> str:
    parts: list[str] = []
    parts.extend(table.leading_lines)
    parts.append(table.header_line)
    parts.append(table.separator_line)
    parts.extend(row.raw_line for row in table.rows)
    parts.extend(table.trailing_lines)
    body = table.newline.join(parts)
    if table.trailing_newline and not body.endswith(("\n", "\r\n")):
        body += table.newline
    return body


def save_table(table: MarkdownTable, path: Path | None = None) -> Path:
    target = path or table.path
    target.write_text(render_table(table), encoding="utf-8")
    table.path = target
    return target
