from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_pairs(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Path B critic training scaffold for ORPO/SimPO.")
    parser.add_argument("--pairs", type=Path, default=Path("training_data/path_b_preference_pairs.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("training/training_run.log"))
    parser.add_argument("--algorithm", choices=["orpo", "simpo"], default="orpo")
    parser.add_argument("--backbone", default="Qwen/Qwen2.5-0.5B-Instruct")
    args = parser.parse_args()

    pairs = load_pairs(args.pairs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "\n".join(
            [
                "Path B critic training scaffold",
                f"algorithm={args.algorithm}",
                f"backbone={args.backbone}",
                f"preference_pairs={len(pairs)}",
                "status=not_run_in_local_repo",
                "next_step=run ORPO/SimPO with Unsloth or TRL on Colab/RunPod and replace this log",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Prepared training log for {len(pairs)} pairs at {args.output}")


if __name__ == "__main__":
    main()

