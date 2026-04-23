# Tenacious Conversion Engine

This repository contains the Week 10 interim build for the Tenacious Consulting and Outsourcing conversion engine challenge.

The current scope covers:

- a local end-to-end thin slice for one synthetic prospect
- an enrichment pipeline that produces hiring-signal and competitor-gap briefs
- email-first outreach with SMS only as a warm-lead scheduling fallback
- Cal.com booking and HubSpot sync as downstream operational writes
- step-level tracing and runtime artifact persistence
- a tau2-bench scaffold with score and trace log contracts

## Quick Start

```bash
python3 -m agent.main
```

## Key Outputs

- Runtime artifacts: [artifacts/runtime](artifacts/runtime)
- Trace log: [artifacts/traces/agent_trace_log.jsonl](artifacts/traces/agent_trace_log.jsonl)
- Evaluation scaffold: [eval](eval)
- Interim report: [docs/interim_submission_report.md](docs/interim_submission_report.md)
