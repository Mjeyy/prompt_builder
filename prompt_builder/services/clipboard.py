import subprocess


class ClipboardError(Exception):
    pass


def copy_to_clipboard(text: str) -> None:
    try:
        result = subprocess.run(
            ["pbcopy"],
            input=text.encode("utf-8"),
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ClipboardError("Команда pbcopy не найдена (требуется macOS)") from exc

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        message = stderr or f"pbcopy завершился с кодом {result.returncode}"
        raise ClipboardError(message)
