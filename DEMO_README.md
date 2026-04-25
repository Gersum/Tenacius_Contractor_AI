# Tenacious Conversion Engine Demo Guide

This guide is for demonstrating the local Week 10 build end to end from the browser operator console.

The goal of the demo is to show, in one flow, that the system can:

- run enrichment for a synthetic lead
- generate the email-first outreach flow
- simulate a reply and qualify it
- create a Cal.com booking artifact that shows whether the run used live API mode or fallback mode
- create the HubSpot artifact with enrichment fields
- send the SMS warm-lead scheduling confirmation
- expose runtime traces and evaluation evidence in the UI

## 1. Start the Demo Server

From the project root:

```bash
python3 visualization/server.py
```

When the server starts, open:

```text
http://127.0.0.1:8000/visualization/
```

If you already have the page open and the API badge says `Static mode only`, refresh the page after starting the server.

## 2. Confirm the UI Is Live

At the top of the page, check the operator status card.

What you should see:

- `Operator API online`
- buttons for `Run Full Pipeline`, `Recompute Tau Score`, and `Refresh Evidence`
- a synthetic lead form with company, domain, contact, email, and phone

Why this matters:

- this confirms the UI is not just a static file viewer
- the page can trigger backend actions directly from the browser

## 3. Run the Full Demo Flow

Leave the default synthetic lead in place, or edit the form fields if you want to show a custom input.

Click:

```text
Run Full Pipeline
```

What the UI should update with:

- the status line changes to `Created lead_<id>`
- the Summary panel updates to the new `lead_id`
- the Workflow panel shows the sequence through enrichment, email, reply, qualification, booking, SMS, and HubSpot
- the Traces panel refreshes with the latest step log

What this proves:

- one click from the UI executes the local orchestration pipeline
- the operator console is the primary demo surface

## 4. Walk Through the Main Panels

Use the four main panels in this order.

### Summary

Show that the new lead reached:

- `booked`
- booking status `booked`
- trace count for the run
- tau baseline summary values

### Signals

Show the enrichment fields:

- `recent_funding`
- `job_post_velocity`
- `layoffs`
- `leadership_change`
- `AI maturity`

What to say:

- these are the public-signal inputs that drive prospect classification and pitch selection

### Operations

Show the operational outputs:

- Email status
- SMS status
- HubSpot status
- Cal.com booking URL
- Discovery brief path
- Evidence graph path

What to say:

- this is the channel hierarchy in action: email first, SMS after warm intent, then discovery-call handoff

### Traces

Show the latest steps, including:

- `send_email`
- `receive_reply`
- `qualify_reply`
- `book_calcom_meeting`
- `send_sms_schedule_confirmation`
- `sync_hubspot_record`

What to say:

- every major action is trace-backed and visible in the demo surface

## 5. Use Artifact Explorer

At the bottom of the page, use the `Select artifact` dropdown.

Recommended order:

1. `email outbound`
2. `hiring signal`
3. `competitor gap`
4. `hubspot`
5. `calcom`
6. `agent traces`
7. `eval score log`
8. `evidence graph`

What to call out in each artifact:

- `email outbound`: shows the generated first-touch email artifact
- `hiring signal`: shows structured enrichment output
- `competitor gap`: shows the research hook and gap framing
- `hubspot`: shows ICP segment, confidence, enrichment timestamp, and signal details
- `calcom`: shows the booking artifact, booking mode, and any fallback reason
- `agent traces`: shows per-step runtime logs
- `eval score log`: shows the tau2 baseline and reproduction-check summary
- `evidence graph`: shows how claims map back to traceable sources

## 6. Recompute Tau Evaluation Evidence

Click:

```text
Recompute Tau Score
```

What should happen:

- the status line updates with the pass@1 value
- the score log is regenerated from `eval/trace_log.jsonl`
- the Summary panel still reflects the tau baseline values

What this proves:

- the evaluation evidence can be refreshed directly from the UI
- the demo includes both production flow evidence and benchmark evidence

## 7. Refresh Without Re-running

Click:

```text
Refresh Evidence
```

Use this when:

- you want to reload the latest artifacts after inspecting files outside the UI
- you want to show that the page can resync without creating a new run

## 8. Suggested Live Narration

Use this short sequence during the demo:

1. Start on the operator card and note that the UI is live, not static.
2. Click `Run Full Pipeline`.
3. Show the new `lead_id` in Summary.
4. Move to Signals and explain the enrichment inputs.
5. Move to Operations and explain the email-primary, SMS-secondary flow.
6. Open `hubspot` in Artifact Explorer and point out the enrichment timestamp plus signal fields.
7. Open `calcom` and `email outbound`.
8. Click `Recompute Tau Score`.
9. Open `eval score log` and `evidence graph`.

This usually gives the cleanest story from operator action to evidence.

## 9. Files Used in the Demo

Primary browser entry point:

- [visualization/index.html](/Users/gersumasfaw/Downloads/week_10/visualization/index.html)

Operator server:

- [visualization/server.py](/Users/gersumasfaw/Downloads/week_10/visualization/server.py)

Latest runtime manifest:

- [artifacts/runtime/current-run.json](/Users/gersumasfaw/Downloads/week_10/artifacts/runtime/current-run.json)

Latest trace log:

- [artifacts/traces/agent_trace_log.jsonl](/Users/gersumasfaw/Downloads/week_10/artifacts/traces/agent_trace_log.jsonl)

Evaluation evidence:

- [eval/score_log.json](/Users/gersumasfaw/Downloads/week_10/eval/score_log.json)
- [eval/trace_log.jsonl](/Users/gersumasfaw/Downloads/week_10/eval/trace_log.jsonl)

Evidence mapping:

- [evidence_graph.json](/Users/gersumasfaw/Downloads/week_10/evidence_graph.json)

## 10. Troubleshooting

If the UI does not update when you click buttons:

- make sure the page is opened through `python3 visualization/server.py`
- check that the top badge says `Operator API online`
- refresh the browser tab once after restarting the server

If port `8000` is already in use:

- stop the previous process on that port
- restart `python3 visualization/server.py`

If the UI loads but artifacts look old:

- click `Refresh Evidence`
- or click `Run Full Pipeline` again to create a fresh run
