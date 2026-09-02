"""The dataset is real and structured; the harness measures memory recall."""

import scripts.generate_dataset as gen
from app.dataset import load_tasks
from app.dataset.harness import run_harness


def test_generated_dataset_is_large_and_structured():
    tasks = gen.build_dataset()
    assert len(tasks) >= 60
    # Every task carries the structure the harness needs.
    for t in tasks:
        assert t.request and t.expected_subtasks and t.reviewer_rubric
        assert t.complexity_tier in {"low", "medium", "high"}
    assert len({t.category for t in tasks}) >= 6
    assert any(t.family for t in tasks)  # deliberately repeated families exist


def test_dataset_file_loads():
    tasks = load_tasks()
    assert len(tasks) >= 60
    assert tasks[0].task_id


def test_harness_shows_memory_recall_on_repeated_family():
    tasks = gen.build_dataset()
    # First 12 include the repeated "vendor_pricing" family.
    report = run_harness(tasks, limit=12)

    assert report["tasks"] == 12
    assert "by_category" in report and "by_tier" in report
    mem = report["memory"]
    assert mem["family_tasks"] >= 5
    # Repeats recall the first occurrence; the first one had nothing to recall.
    assert mem["repeat_occurrence_recall_rate"] > 0.5
    assert mem["first_occurrence_recall_rate"] == 0.0
