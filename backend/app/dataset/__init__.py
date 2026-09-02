"""Dataset loading + the default location of the generated task file."""

from __future__ import annotations

from pathlib import Path

from .schema import AgenticTask

DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "agentic_tasks" / "tasks.jsonl"


def load_tasks(path: Path | str = DATASET_PATH) -> list[AgenticTask]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Dataset not found at {p}. Generate it with "
            "`python -m scripts.generate_dataset`."
        )
    tasks = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            tasks.append(AgenticTask.model_validate_json(line))
    return tasks


__all__ = ["AgenticTask", "DATASET_PATH", "load_tasks"]
