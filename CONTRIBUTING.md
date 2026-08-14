# Разработка Prompt Builder

Для пользователей: [README.md](README.md) и [RUNBOOK.md](RUNBOOK.md).

## Слои

```text
data/  →  parsers  →  services  →  cli / gui
                 ↖ models, paths
```

- Шаблоны только в `data/`. Пути только через `prompt_builder.paths`.
- `parsers/` читают markdown. `services/` подставляют плейсхолдеры, буфер, QA таблиц.
- `cli/` — меню терминала. `gui/` — окно. Не импортировать GUI из CLI и наоборот.
- Подписи режимов — из `WORK_MODE_LABELS` / `CATEGORY_LABELS` в `models.py`.

## Окружение и тесты

```bash
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

Новые зависимости не добавлять без необходимости. Тесты — `unittest` из стандартной библиотеки.

## Когда обновлять документы

Одно изменение кода = те же документы в том же коммите / том же ответе агента.

| Что изменилось | Куда писать |
|----------------|-------------|
| Поведение для пользователя: режимы, кнопки, пути к данным, плейсхолдеры | README + RUNBOOK + CHANGELOG |
| Установка, запуск, типичные ошибки | RUNBOOK + CHANGELOG |
| Только внутренний рефакторинг, UX тот же | CHANGELOG (кратко). README не трогать |
| Новый или переименованный файл данных | дерево в README и RUNBOOK, раздел «Как обновлять данные», CHANGELOG |

Правила для Cursor лежат в `.cursor/rules/`. Не использовать устаревший `.cursorrules`.

Не оставлять шаблоны в корне репозитория и не возвращать имя `horoscop`.
