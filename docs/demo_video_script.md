# Demo Video Script and Commands

This runbook is the fastest truthful way to record the Week 10 demo in under 8 minutes with **no external logins on camera**.

## What This Repo Can Honestly Show

The current codebase can show, end to end:

- a synthetic prospect flowing through enrichment
- a signal-grounded outbound email artifact
- a synthetic inbound reply
- qualification and booking orchestration
- hiring-signal and competitor-gap briefs with visible confidence scores
- a Cal.com booking through the local self-hosted instance
- a HubSpot-shaped contact snapshot updating in real time in the operator UI

The current codebase does **not** yet support true live:

- Resend or MailerSend delivery
- inbound email webhooks from a real mailbox
- HubSpot cloud writes

So for the video, present the email and HubSpot parts as a **no-login local operator demo with artifact-backed channel and CRM steps**. That keeps the demo accurate and still satisfies the requirement that the reviewer does not need to log in anywhere.

## One-Time Setup Before Recording

### Terminal 1: start Cal.com

```bash
docker compose -f /Users/gersumasfaw/Downloads/week_10/infra/docker-compose.yml up -d
```

### Terminal 2: start the operator UI

```bash
cd /Users/gersumasfaw/Downloads/week_10
python3 visualization/server.py
```

### Optional reset before recording

If you want a clean visible run, remove only the current-run manifest and let the next run regenerate it:

```bash
rm -f /Users/gersumasfaw/Downloads/week_10/artifacts/runtime/current-run.json
```

## Recording URL

Open this in the browser:

```text
http://127.0.0.1:8000/visualization/
```

## Recommended Lead Input

Use the default synthetic lead unless you want to customize the form:

- Company: `Vercel`
- Domain: `vercel.com`
- Contact: `Alex Morgan`
- Email: `alex.morgan@example.com`
- Phone: `+251911000000`

## 8-Minute Demo Script

### 0:00 to 0:30 — frame the demo

Narration:

> This is the Tenacious conversion engine running locally with no reviewer login required. I’m going to show a synthetic prospect moving from signal enrichment through outbound email, reply handling, qualification, scheduling through local Cal.com, and CRM population in one operator flow.

Show:

- top status badge
- lead form
- `Run Full Pipeline` button

### 0:30 to 1:15 — run the pipeline

Action:

- Click `Run Full Pipeline`

Narration:

> One click runs the full orchestration pipeline. The workflow is email-first, SMS only after warm intent, and then a discovery-call handoff.

Show after completion:

- Summary panel
- new `lead_id`
- booking status

### 1:15 to 2:30 — show hiring-signal brief

Open Artifact Explorer:

- select `hiring signal`

Narration:

> This is the hiring-signal brief generated for the prospect. It includes funding, job-post signal, layoff signal, leadership change signal, and AI maturity scoring. The important thing to notice is that each signal carries a confidence field rather than a bare claim.

Call out explicitly:

- `funding_signal`
- `job_post_signal`
- `layoff_signal`
- `leadership_change_signal`
- `ai_maturity_score`
- confidence values on the signal objects

### 2:30 to 3:20 — show competitor-gap brief

Open Artifact Explorer:

- select `competitor gap`

Narration:

> Here is the competitor-gap brief. This is the research layer that turns the outreach from a generic pitch into a finding. In the current implementation it is heuristic rather than a full top-quartile peer model, so I present it as a generated local brief, not as a live external benchmark system.

Call out:

- top findings
- evidence-backed wording
- any confidence-bearing structure visible in the brief

### 3:20 to 4:10 — show outbound email and reply flow

Open Artifact Explorer:

- select `email outbound`

Narration:

> This is the signal-grounded outreach email artifact. In this repo, outbound email is still a sink-backed adapter, so the demo shows the exact generated message and delivery artifact without requiring a real mailbox login on camera.

Then move to traces panel and point out:

- `send_email`
- `receive_reply`
- `qualify_reply`

Narration:

> The reply step is simulated locally, which lets the reviewer see the qualification and handoff logic without relying on an external inbox.

### 4:10 to 5:20 — show Cal.com booking

Open Artifact Explorer:

- select `calcom`

Narration:

> This step books the discovery call through local Cal.com. The artifact shows the booking URL, provider, host, scheduled time, and whether the system used live local API mode or fell back. For the recording, we want this to show a real local booking, not simulated fallback.

Call out:

- `provider`
- `booking_url`
- `scheduled_for`
- `status`
- `mode`

If the run succeeded live, say:

> This booking was created against the local Cal.com instance running on localhost, so the reviewer does not need any external login to verify the flow.

### 5:20 to 6:20 — show HubSpot contact snapshot

Open Artifact Explorer:

- select `hubspot`

Narration:

> This is the HubSpot-shaped contact record generated in real time after qualification and booking. In the current repo, HubSpot is a local snapshot writer rather than a cloud CRM integration, but the demo still shows all of the fields the downstream sales owner would inherit.

Call out explicitly:

- enrichment timestamp
- non-null signal fields
- ICP segment
- confidence
- booking metadata

### 6:20 to 7:00 — show workflow proof

Stay in the UI and point to:

- workflow panel
- traces panel

Narration:

> The important engineering point is that every stage is trace-backed: enrichment, outbound email, inbound reply, qualification, booking, SMS follow-up, and CRM sync all appear in the runtime log.

### 7:00 to 7:40 — show evaluation evidence

Action:

- Click `Recompute Tau Score`
- Open `eval score log`
- Open `evidence graph`

Narration:

> The same operator surface can also refresh the evaluation evidence, so the demo shows both the production-style conversion flow and the benchmark evidence chain from one browser session.

### 7:40 to 8:00 — close clearly

Narration:

> So the full no-login demo shows a synthetic prospect moving from enrichment to a signal-grounded outreach artifact, reply qualification, local Cal.com booking, and HubSpot-shaped CRM population, all backed by local traces and evidence artifacts.

## Commands to Keep Nearby During Recording

### Health check the operator UI

```bash
curl -s http://127.0.0.1:8000/api/health
```

### Health check local Cal.com web app

```bash
curl -s http://127.0.0.1:3004 | head
```

### Run the pipeline directly from the terminal if the UI button fails

```bash
cd /Users/gersumasfaw/Downloads/week_10
python3 -m agent.main
```

### Re-open the latest generated manifest

```bash
cat /Users/gersumasfaw/Downloads/week_10/artifacts/runtime/current-run.json
```

## Presenter Notes

- Do not claim that the email was sent through a live mailbox. Call it a generated outbound email artifact.
- Do not claim that HubSpot is a live cloud write. Call it a HubSpot-shaped local contact snapshot.
- Do claim that Cal.com is local and can be shown without external login if the booking artifact says live booking succeeded.
- If Cal.com falls back, stop and rerun before recording. The demo brief specifically wants the call booked via Cal.com.
