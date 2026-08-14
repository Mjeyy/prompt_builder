from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
DOCS_SAMPLES_DIR = DOCS_DIR / "samples"

AUTOS_PATH = DATA_DIR / "autos.md"
REPAIR_PROMPTS_PATH = DATA_DIR / "repair_prompts.md"
TUNING_PROMPTS_PATH = DATA_DIR / "tuning_prompts.md"
HOROSCOPE_AUTO_PATH = DATA_DIR / "horoscope_auto.md"
HOROSCOPE_DATE_PATH = DATA_DIR / "horoscope_date.md"
LINKS_PATH = DATA_DIR / "links.md"
