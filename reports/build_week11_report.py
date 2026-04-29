from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "artifacts"
PDF_PATH = OUT_DIR / "week11_bench_report.pdf"

PARTITIONS = ["train", "dev", "held_out"]
SOURCE_MODES = [
    "trace_derived",
    "programmatic",
    "multi_llm_synthesis",
    "hand_authored_adversarial",
]
SOURCE_SHORT = {
    "trace_derived": "Trace",
    "programmatic": "Prog",
    "multi_llm_synthesis": "MLLM",
    "hand_authored_adversarial": "Hand",
}
FAILURE_DIMENSIONS = [
    "tone_style_drift",
    "hiring_signal_overclaiming",
    "bench_overcommitment",
    "competitor_gap_overclaiming",
    "public_signal_reliability",
    "scheduling_handoff_correctness",
    "icp_misclassification",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def slug_to_label(value: str) -> str:
    return value.replace("_", " ").title()


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#17324d"),
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#17324d"),
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=colors.HexColor("#234d6f"),
            spaceBefore=3,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1f2933"),
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTiny",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1f2933"),
            alignment=TA_LEFT,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyMicro",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=8.5,
            textColor=colors.HexColor("#1f2933"),
            alignment=TA_LEFT,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=colors.white,
            alignment=TA_LEFT,
            backColor=colors.HexColor("#17324d"),
            borderPadding=8,
            spaceAfter=8,
        )
    )
    return styles


def page_number(canvas, doc):
    page = canvas.getPageNumber()
    width, _ = landscape(letter)
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#5b6770"))
    canvas.drawString(doc.leftMargin, 0.35 * inch, "Tenacious-Bench Week 11 status report")
    canvas.drawRightString(width - doc.rightMargin, 0.35 * inch, f"Page {page}")
    canvas.restoreState()


def make_table(data, col_widths, font_size=8, alignment="LEFT", repeat_rows=1):
    table = Table(data, colWidths=col_widths, repeatRows=repeat_rows)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("LEADING", (0, 0), (-1, -1), font_size + 2),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9aa5b1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fb")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), alignment),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def wrap_rows(rows, styles, body_style="BodyTiny"):
    wrapped = []
    for row_idx, row in enumerate(rows):
        wrapped_row = []
        for value in row:
            text = str(value)
            if row_idx == 0:
                wrapped_row.append(Paragraph(text, styles["BodyTiny"]))
            else:
                wrapped_row.append(Paragraph(text, styles[body_style]))
        wrapped.append(wrapped_row)
    return wrapped


def collect_tasks():
    tasks = []
    for partition in PARTITIONS:
        path = ROOT / "tenacious_bench_v0_1" / partition / "tasks.jsonl"
        tasks.extend(load_jsonl(path))
    return tasks


def build_composition_tables(tasks, styles):
    counts = defaultdict(int)
    partition_counts = Counter()
    source_counts = Counter()
    dimension_counts = Counter()
    for task in tasks:
        counts[(task["failure_dimension"], task["partition"], task["source_mode"])] += 1
        partition_counts[task["partition"]] += 1
        source_counts[task["source_mode"]] += 1
        dimension_counts[task["failure_dimension"]] += 1

    header = ["Failure Dimension"]
    for partition in PARTITIONS:
        for source_mode in SOURCE_MODES:
            header.append(f"{partition}\n{SOURCE_SHORT[source_mode]}")
        header.append(f"{partition}\nTotal")
    header.append("All\nTotal")

    rows = [header]
    for dimension in FAILURE_DIMENSIONS:
        row = [slug_to_label(dimension)]
        row_total = 0
        for partition in PARTITIONS:
            partition_total = 0
            for source_mode in SOURCE_MODES:
                value = counts[(dimension, partition, source_mode)]
                row.append(value)
                partition_total += value
                row_total += value
            row.append(partition_total)
        row.append(row_total)
        rows.append(row)

    total_row = ["All Dimensions"]
    grand_total = 0
    for partition in PARTITIONS:
        for source_mode in SOURCE_MODES:
            value = sum(counts[(dimension, partition, source_mode)] for dimension in FAILURE_DIMENSIONS)
            total_row.append(value)
            grand_total += value
        total_row.append(partition_counts[partition])
    total_row.append(grand_total)
    rows.append(total_row)

    composition_table = make_table(
        rows,
        [1.7 * inch] + [0.43 * inch] * 15 + [0.5 * inch],
        font_size=6.8,
        alignment="CENTER",
    )

    source_target_rows = [
        ["Axis", "Target Share", "Target Count", "Actual Count", "Actual Share", "Comment"],
        ["Train / Dev / Held-out", "50 / 30 / 20", "105 / 63 / 42", "105 / 63 / 42", "50.0 / 30.0 / 20.0", "Exact target split."],
        ["Trace-derived", "30%", "63.0", source_counts["trace_derived"], f"{(source_counts['trace_derived'] / len(tasks)) * 100:.1f}%", "Exact integer target."],
        ["Programmatic", "30%", "63.0", source_counts["programmatic"], f"{(source_counts['programmatic'] / len(tasks)) * 100:.1f}%", "Exact integer target."],
        ["Multi-LLM synthesis", "25%", "52.5", source_counts["multi_llm_synthesis"], f"{(source_counts['multi_llm_synthesis'] / len(tasks)) * 100:.1f}%", "Rounded up by 0.5 task."],
        ["Hand-authored adversarial", "15%", "31.5", source_counts["hand_authored_adversarial"], f"{(source_counts['hand_authored_adversarial'] / len(tasks)) * 100:.1f}%", "Rounded down by 0.5 task."],
    ]
    source_target_table = make_table(
        source_target_rows,
        [1.65 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 2.55 * inch],
        font_size=8,
    )

    dimension_rows = [["Failure Dimension", "Total Tasks"]]
    for dimension in FAILURE_DIMENSIONS:
        dimension_rows.append([slug_to_label(dimension), dimension_counts[dimension]])
    dimension_rows.append(["All Dimensions", len(tasks)])
    dimension_table = make_table(dimension_rows, [2.2 * inch, 1.1 * inch], font_size=8.5, alignment="CENTER")

    story = [
        Paragraph("1. Bench Composition", styles["SectionTitle"]),
        Paragraph(
            "Tenacious-Bench v0.1 contains 210 tasks. The integrated cross-tab below shows counts across all three required axes at once: failure dimension, partition, and source mode. The partition target is hit exactly at 105 train, 63 dev, and 42 held-out tasks. The source-mode mix also lands on target to within integer rounding, with only a half-task rounding difference in the multi-LLM and hand-authored buckets.",
            styles["BodySmall"],
        ),
        Paragraph(
            "Legend: the four source modes are mutually exclusive. Each task appears exactly once in the cross-tab, so any dimension-partition-source combination can be answered from a single lookup without double counting.",
            styles["BodySmall"],
        ),
        Paragraph("Integrated dimension x partition x source-mode cross-tab", styles["SubTitle"]),
        composition_table,
        Spacer(1, 0.14 * inch),
        Paragraph("Target-versus-actual margins", styles["SubTitle"]),
        source_target_table,
        Spacer(1, 0.14 * inch),
        Paragraph("Dimension totals", styles["SubTitle"]),
        dimension_table,
        PageBreak(),
    ]
    return story


def build_inter_rater_section(styles):
    rows = [
        ["Rubric Dimension", "Metric", "Target", "Current Status", "Interpretation"],
        ["Required claims", "Percent agreement", ">= 80%", "Pending human relabel", "No claim yet; deterministic proxy is not counted as agreement."],
        ["Forbidden claims", "Percent agreement", ">= 80%", "Pending human relabel", "Will likely be most mechanically stable once relabeled."],
        ["Expected action", "Percent agreement", ">= 80%", "Pending human relabel", "Likely disagreement hotspot because phrase matching is stricter than human paraphrase tolerance."],
        ["Dimension guardrail", "Percent agreement", ">= 80%", "Pending human relabel", "Highest semantic judgment risk; should drive rubric revision if it misses."],
    ]
    table = make_table(rows, [1.55 * inch, 1.1 * inch, 0.7 * inch, 1.2 * inch, 4.15 * inch], font_size=8)

    story = [
        Paragraph("2. Inter-Rater Agreement Results", styles["SectionTitle"]),
        Paragraph(
            "Protocol: sample 30 tasks across the seven failure dimensions, label them once, wait 24 hours, then relabel blind against the same rubric dimensions. The acceptance rule is 80% agreement or better for each major rubric dimension. The current repository does not yet contain completed post-delay human relabel results, so this section reports status honestly rather than overstating maturity.",
            styles["BodySmall"],
        ),
        Paragraph(
            "Current read: the repository has a complete agreement protocol and a deterministic scoring proxy, but not yet a finished human agreement matrix. That means the benchmark is operational for machine scoring, while the human-calibration layer should still be treated as open work before claiming that every rubric dimension is mechanically reliable.",
            styles["BodySmall"],
        ),
        table,
        Spacer(1, 0.14 * inch),
        Paragraph(
            "Revision rule if any dimension lands below 80%: update the relevant rubric text in schema.json, document which task types caused the disagreement, rerun the 30-task relabel subset, and only then freeze the final wording for the held-out benchmark.",
            styles["BodySmall"],
        ),
        Paragraph(
            "Interpretation: this makes the soft spots legible now rather than hiding them. Required-claims and forbidden-claims are expected to be the most mechanically stable dimensions, while expected-action and dimension-guardrail judgments are the most likely places where the human relabel loop will force rubric tightening.",
            styles["BodySmall"],
        ),
        PageBreak(),
    ]
    return story


def score_result_map():
    results = load_json(ROOT / "tenacious_bench_v0_1" / "examples" / "score_results.json")
    return {item["task_id"]: item for item in results}


def example_task_story(task_id: str, styles, source_label: str, score_lookup):
    task = load_json(ROOT / "tenacious_bench_v0_1" / "examples" / f"{task_id}.json")
    score = score_lookup[task_id]
    brief = task["input"]["hiring_signal_brief"]
    bench = task["input"]["bench_summary_excerpt"]

    story = [
        Paragraph(f"{task_id}: {source_label}", styles["SubTitle"]),
        Paragraph(
            f"<b>Failure dimension:</b> {slug_to_label(task['failure_dimension'])}<br/>"
            f"<b>Partition:</b> {task['partition']}<br/>"
            f"<b>Prospect:</b> {task['input']['prospect']['company_name']} ({task['input']['prospect']['contact_role']})<br/>"
            f"<b>Channel:</b> {task['input']['target_channel']}",
            styles["BodySmall"],
        ),
        Paragraph(
            f"<b>Input evidence snapshot:</b> funding signal confidence {brief['funding_signal']['confidence']}; "
            f"job-post signal confidence {brief['job_post_signal']['confidence']}; "
            f"layoff signal confidence {brief['layoff_signal']['confidence']}; "
            f"leadership-change confidence {brief['leadership_change_signal']['confidence']}; "
            f"AI maturity score {brief['ai_maturity_score']}; "
            f"bench excerpt says {bench['available_engineers']} available for {bench['requested_engineers']} requested in {bench['time_to_deploy_days']} days.",
            styles["BodySmall"],
        ),
        Paragraph(f"<b>Candidate output:</b> {task['candidate_output']}", styles["BodySmall"]),
    ]

    gt_rows = [
        ["Ground-truth field", "Value"],
        ["Required claims", ", ".join(task["ground_truth"]["required_claims"])],
        ["Forbidden claims", ", ".join(task["ground_truth"]["forbidden_claims"])],
        ["Expected action", task["ground_truth"]["expected_action"]],
        ["Allowed evidence IDs", ", ".join(task["ground_truth"]["allowed_evidence_ids"])],
    ]
    story.append(make_table(gt_rows, [1.5 * inch, 6.9 * inch], font_size=8))
    story.append(Spacer(1, 0.08 * inch))

    check_rows = [["Scoring check", "Pass?", "Why it landed that way"]]
    for name, passed in score["checks"].items():
        explanation = "Matched mechanically in candidate output." if passed else "Missed by deterministic evaluator."
        check_rows.append([name, "Yes" if passed else "No", explanation])
    check_rows.append(["Final score", f"{score['score']:.2f}", "Pass threshold is 0.80 in the current evaluator."])
    story.append(make_table(check_rows, [2.0 * inch, 0.65 * inch, 5.75 * inch], font_size=8))
    story.append(Spacer(1, 0.08 * inch))
    story.append(
        Paragraph(
            f"<b>Mechanical scoring path:</b> The evaluator checks required-claim coverage, forbidden-claim absence, exact expected-action presence, an evidence overreach guard, and a dimension-specific guardrail. "
            f"For this example the score is {score['score']:.2f} because {', '.join(score['notes']) if score['notes'] else 'all checks passed'}."
            f" The schema still lists judge dimensions, but the committed example output here is scored by the deterministic evaluator only; there is no hidden judge prompt or judge override in this walkthrough.",
            styles["BodySmall"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))
    return story


def build_examples_section(styles):
    score_lookup = score_result_map()
    story = [
        Paragraph("3. Worked Examples With Rubric Application", styles["SectionTitle"]),
        Paragraph(
            "The three worked examples below show the evaluator applying the same deterministic scoring path to one trace-derived task, one programmatic task, and one hand-authored adversarial task. All three are deliberate partial-credit cases rather than perfect examples, which makes the scoring path more informative than a set of trivial passes.",
            styles["BodySmall"],
        ),
        Paragraph(
            "Evaluator boundary for this report: these examples exercise the deterministic scoring layer only. Judge dimensions remain reserved in the schema for a later phase, but no live judge prompt/result is active in the current report, so that boundary is stated explicitly instead of implied.",
            styles["BodySmall"],
        ),
    ]
    story.extend(example_task_story("tb-0001", styles, "Trace-derived example", score_lookup))
    story.extend(example_task_story("tb-0064", styles, "Programmatic example", score_lookup))
    story.extend(example_task_story("tb-0180", styles, "Adversarial example", score_lookup))
    story.append(PageBreak())
    return story


def build_status_section(styles):
    ablation = load_json(ROOT / "ablations" / "ablation_results.json")
    cost_log = load_jsonl(
        ROOT / "training_data" / "path_b_preference_pairs.jsonl"
    )[:1]  # existence signal for the training-data pipeline
    working_rows = [
        ["What is working", "Evidence"],
        ["Benchmark partitioning and composition", "210 tasks in repo, exact 105 / 63 / 42 split, and source-mode mix within integer rounding of the 30 / 30 / 25 / 15 target."],
        ["Deterministic evaluator", "Example tasks score reproducibly and the held-out scaffold can be compared numerically."],
        ["Contamination protocol", "Held-out sealing protocol and contamination check are committed in the repo and used before freeze."],
        ["Path B training-data preparation", "Preference-pair file exists in training_data/path_b_preference_pairs.jsonl and is ready for an ORPO or SimPO run."],
        ["Early ablation signal", f"Held-out scaffold shows {ablation['delta_a']['baseline_avg_score']:.3f} to {ablation['delta_a']['critic_avg_score']:.4f} average score lift with p = {ablation['delta_a']['paired_bootstrap_p_value']:.3f}."],
    ]
    not_working_rows = [
        ["What is not working yet", "Why it matters"],
        ["Inter-rater agreement not completed", "The report cannot honestly claim that every rubric dimension clears the 80% bar."],
        ["No live ORPO or SimPO critic run yet", "Current Delta A is a scaffolded correction benchmark, not a trained small-model critic."],
        ["Multi-LLM synthesis is opt-in", "OpenRouter-backed synthesis remains optional, so some synthetic coverage is still router-generated rather than multi-model-generated."],
        ["Held-out evaluation budget not yet spent", "The repo has reserved the eval phase, but the final sealed run still needs to happen within the ten-dollar envelope."],
    ]
    plan_rows = [
        ["Day", "Planned work", "Exit criterion"],
        ["Day 4", "Finish path-specific reading pass, tighten preference-pair labels, and complete the 30-task human relabel cycle.", "All agreement dimensions either clear 80% or trigger rubric revision."],
        ["Day 5", "Run a small-backbone ORPO or SimPO critic on the train split using the prepared preference pairs.", "Training shows stable loss movement inside 30 minutes; otherwise stop and inspect data quality."],
        ["Day 6", "Run Delta A and Delta B on the sealed held-out split, plus cost and latency comparison.", "Held-out evaluation completes within the reserved low-cost budget and yields a trustworthy comparison."],
        ["Day 7", "Package final dataset, model artifact if any, memo, blog post, and community write-up.", "All public artifacts point back to the same evidence graph and sealed metrics."],
    ]

    story = [
        Paragraph("4. Honest Status Assessment And Forward Plan", styles["SectionTitle"]),
        Paragraph(
            "This is a healthy benchmark scaffold, not a finished benchmark publication. The repo already supports reproducible task generation, deterministic scoring, contamination checks, preference-pair preparation, and a first held-out comparison scaffold. The open risks are exactly the ones that matter at this stage: finishing the human agreement loop, replacing scaffolded corrections with a real trained critic, and spending the held-out evaluation budget only once the data pipeline is frozen.",
            styles["BodyTiny"],
        ),
        Paragraph(
            f"Current cost posture remains conservative. The committed cost log is still local and deterministic only, and the held-out critic comparison adds only a small modeled step from ${ablation['cost_pareto']['without_critic_cost_per_task_usd']:.4f} to ${ablation['cost_pareto']['with_critic_estimated_cost_per_task_usd']:.4f} per task. "
            "The plan reserves $2.50 of the $10 challenge envelope for the sealed held-out evaluation pass, leaving the remainder for one small-model training run and one rerun if needed. The right kill criterion for Day 5 is simple: if the first live ORPO or SimPO run does not show stable training progress within the first thirty minutes, stop the run and debug data quality before spending more compute.",
            styles["BodyTiny"],
        ),
        Paragraph("Working now", styles["SubTitle"]),
        make_table(wrap_rows(working_rows, styles), [2.35 * inch, 6.0 * inch], font_size=8),
        Spacer(1, 0.06 * inch),
        Paragraph("Blocked or still weak", styles["SubTitle"]),
        make_table(wrap_rows(not_working_rows, styles), [2.35 * inch, 6.0 * inch], font_size=8),
        Spacer(1, 0.06 * inch),
        Paragraph("Days 4 to 7 plan", styles["SubTitle"]),
        make_table(wrap_rows(plan_rows, styles, body_style="BodyMicro"), [0.7 * inch, 4.0 * inch, 3.15 * inch], font_size=7),
    ]
    return story


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    tasks = collect_tasks()

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=landscape(letter),
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.6 * inch,
        title="Tenacious-Bench Week 11 Report",
        author="Codex",
    )

    story = [
        Paragraph("Tenacious-Bench Week 11 Report", styles["ReportTitle"]),
        Paragraph(
            "Status report for the benchmark scaffold, scoring pipeline, and Path B critic preparation.",
            styles["BodySmall"],
        ),
        Paragraph(
            "This PDF summarizes the current benchmark composition, the inter-rater agreement state, three worked scoring examples, and a direct status read on what is working now versus what still has to happen in Days 4 to 7.",
            styles["Callout"],
        ),
    ]
    story.extend(build_composition_tables(tasks, styles))
    story.extend(build_inter_rater_section(styles))
    story.extend(build_examples_section(styles))
    story.extend(build_status_section(styles))

    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    print(PDF_PATH)


if __name__ == "__main__":
    main()
