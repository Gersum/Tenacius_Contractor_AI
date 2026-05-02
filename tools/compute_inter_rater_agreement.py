from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABEL_SHEET = ROOT / "inter_rater" / "label_sheet.csv"
RESULT_JSON = ROOT / "inter_rater" / "agreement_results.json"
RESULT_MD = ROOT / "inter_rater" / "agreement_results.md"

DIMENSIONS = [
    ("required_claims", "Required claims"),
    ("forbidden_claims", "Forbidden claims"),
    ("expected_action", "Expected action"),
    ("dimension_guardrail", "Dimension guardrail"),
]


def parse_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y"}:
        return True
    if normalized in {"0", "false", "f", "no", "n"}:
        return False
    return None


def compute(rows: list[dict[str, str]]) -> dict:
    results = []
    for key, label in DIMENSIONS:
        total = 0
        agreements = 0
        missing = 0
        for row in rows:
            left = parse_bool(row.get(f"{key}_pass1", ""))
            right = parse_bool(row.get(f"{key}_pass2", ""))
            if left is None or right is None:
                missing += 1
                continue
            total += 1
            if left == right:
                agreements += 1
        pct = round((agreements / total) * 100, 1) if total else None
        results.append(
            {
                "key": key,
                "label": label,
                "agreements": agreements,
                "labeled_pairs": total,
                "missing_pairs": missing,
                "agreement_pct": pct,
                "threshold_pct": 80.0,
                "passed": pct is not None and pct >= 80.0,
            }
        )
    return {"task_count": len(rows), "dimensions": results}


def render_markdown(payload: dict) -> str:
    lines = [
        "# Inter-Rater Agreement Results",
        "",
        f"Task count: `{payload['task_count']}`",
        "",
        "| Rubric dimension | Agreements | Labeled pairs | Missing pairs | Agreement % | Threshold | Status |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["dimensions"]:
        pct = "pending" if row["agreement_pct"] is None else f"{row['agreement_pct']:.1f}%"
        status = "pass" if row["passed"] else ("pending" if row["agreement_pct"] is None else "revise")
        lines.append(
            f"| {row['label']} | {row['agreements']} | {row['labeled_pairs']} | {row['missing_pairs']} | {pct} | 80% | {status} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    with LABEL_SHEET.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    payload = compute(rows)
    RESULT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    RESULT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(RESULT_MD)


if __name__ == "__main__":
    main()
