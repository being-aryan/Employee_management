import json
import os
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"


def read_json(filename: str, default_data: Any) -> Any:
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    file_path = DATA_DIRECTORY / filename

    if not file_path.exists():
        write_json(filename, default_data)
        return default_data

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in file: {filename}") from exc


def write_json(filename: str, data: Any) -> None:
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    file_path = DATA_DIRECTORY / filename

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DATA_DIRECTORY,
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(data, file, indent=4, ensure_ascii=False)

        os.replace(temporary_path, file_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
