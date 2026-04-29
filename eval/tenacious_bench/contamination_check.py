from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


STOPWORDS = {
    "case",
    "is",
    "about",
    "at",
    "tenacious",
    "sdr",
    "use",
    "evidence",
    "token",
    "sig",
    "and",
    "respect",
    "the",
    "requested",
    "action",
    "com",
    "example",
}


def normalize(text: str) -> list[str]:
    tokens = [token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOPWORDS]
    marker_tokens = [token for token in tokens if any(char.isdigit() for char in token)]
    return marker_tokens or tokens


def shingles(tokens: list[str], n: int = 8) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def vector(tokens: list[str]) -> Counter[str]:
    return Counter(tokens)


def cosine(a: Counter[str], b: Counter[str]) -> float:
    keys = set(a) | set(b)
    dot = sum(a[k] * b[k] for k in keys)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def task_text(task: dict[str, Any]) -> str:
    task_input = task.get("input", {})
    prospect = task_input.get("prospect", {})
    return " ".join(
        [
            str(prospect.get("company_name", "")),
            str(prospect.get("domain", "")),
            str(prospect.get("contact_role", "")),
            " ".join(task_input.get("prior_thread", [])),
            str(task_input.get("target_channel", "")),
        ]
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check(train_path: Path, held_out_path: Path) -> dict[str, Any]:
    train = load_jsonl(train_path)
    held_out = load_jsonl(held_out_path)
    train_rows = [(task["task_id"], normalize(task_text(task))) for task in train]
    held_rows = [(task["task_id"], normalize(task_text(task))) for task in held_out]

    max_ngram_overlap = 0
    max_cosine = 0.0
    closest_pair: tuple[str, str] | None = None
    for held_id, held_tokens in held_rows:
        held_shingles = shingles(held_tokens)
        held_vec = vector(held_tokens)
        for train_id, train_tokens in train_rows:
            overlap = len(held_shingles & shingles(train_tokens))
            similarity = cosine(held_vec, vector(train_tokens))
            if overlap > max_ngram_overlap or similarity > max_cosine:
                closest_pair = (held_id, train_id)
            max_ngram_overlap = max(max_ngram_overlap, overlap)
            max_cosine = max(max_cosine, similarity)

    time_shift_failures = [
        task["task_id"]
        for task in held_out
        if any("generic placeholder" in ref.lower() for ref in task.get("metadata", {}).get("source_refs", []))
    ]

    passed = max_ngram_overlap == 0 and max_cosine < 0.85 and not time_shift_failures
    return {
        "passed": passed,
        "train_task_count": len(train),
        "held_out_task_count": len(held_out),
        "max_8gram_overlap_count": max_ngram_overlap,
        "max_token_cosine_similarity": round(max_cosine, 4),
        "embedding_similarity_threshold": 0.85,
        "closest_pair": closest_pair,
        "time_shift_failures": time_shift_failures,
        "report_hash": hashlib.sha256(f"{max_ngram_overlap}:{max_cosine}:{time_shift_failures}".encode()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Tenacious-Bench contamination checks.")
    parser.add_argument("--train", type=Path, default=Path("tenacious_bench_v0_1/train/tasks.jsonl"))
    parser.add_argument("--held-out", type=Path, default=Path("tenacious_bench_v0_1/held_out/tasks.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("tenacious_bench_v0_1/contamination_check.json"))
    args = parser.parse_args()
    result = check(args.train, args.held_out)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
