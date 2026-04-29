# Multi-LLM Synthesis Author Prompt

You are generating a synthetic benchmark candidate output for a Tenacious-style B2B sales-agent task.

Requirements:

- return strict JSON with keys `candidate_output` and `author_note`
- produce a concise candidate output, not an explanation
- make the wording diagnostic for the supplied failure dimension
- do not add unsupported evidence beyond the task payload
- preserve the expected business action or the characteristic failure under test

The task payload will provide:

- `task_id`
- `failure_dimension`
- `prospect`
- `ground_truth`

The output should help distinguish bounded, policy-compliant behavior from fluent but wrong behavior.
