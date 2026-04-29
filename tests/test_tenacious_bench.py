from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from eval.tenacious_bench.contamination_check import check
from eval.tenacious_bench.scoring_evaluator import score_task


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class TenaciousBenchTests(unittest.TestCase):
    def test_partitions_have_required_counts_and_fields(self) -> None:
        expected_counts = {"train": 105, "dev": 63, "held_out": 42}
        required = {
            "task_id",
            "partition",
            "source_mode",
            "difficulty",
            "failure_dimension",
            "input",
            "candidate_output",
            "ground_truth",
            "rubric",
            "metadata",
        }
        for partition, expected_count in expected_counts.items():
            rows = load_jsonl(ROOT / "tenacious_bench_v0_1" / partition / "tasks.jsonl")
            self.assertEqual(len(rows), expected_count)
            self.assertTrue(all(required.issubset(row) for row in rows))
            self.assertTrue(all(row["partition"] == partition for row in rows))

    def test_scoring_evaluator_scores_good_and_bad_outputs(self) -> None:
        task = load_jsonl(ROOT / "tenacious_bench_v0_1" / "train" / "tasks.jsonl")[0]
        good = score_task(task)
        bad = score_task(task, "Just checking in about our offshore bench of A-player engineers.")

        self.assertTrue(good.passed)
        self.assertFalse(bad.passed)
        self.assertLess(bad.score, good.score)

    def test_contamination_report_passes_for_generated_partitions(self) -> None:
        result = check(
            ROOT / "tenacious_bench_v0_1" / "train" / "tasks.jsonl",
            ROOT / "tenacious_bench_v0_1" / "held_out" / "tasks.jsonl",
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["max_8gram_overlap_count"], 0)
        self.assertLess(result["max_token_cosine_similarity"], 0.85)

    def test_training_pairs_align_with_train_partition(self) -> None:
        train = load_jsonl(ROOT / "tenacious_bench_v0_1" / "train" / "tasks.jsonl")
        pairs = load_jsonl(ROOT / "training_data" / "path_b_preference_pairs.jsonl")

        self.assertEqual(len(pairs), len(train))
        self.assertTrue(all(pair["chosen_score"] > pair["rejected_score"] for pair in pairs))


if __name__ == "__main__":
    unittest.main()
