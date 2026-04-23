const MANIFEST = "../artifacts/runtime/current-run.json";

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`Failed to load ${path}`);
  return response.json();
}

async function loadText(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`Failed to load ${path}`);
  return response.text();
}

function lines(text) {
  return text.split("\n").map((line) => line.trim()).filter(Boolean).map((line) => JSON.parse(line));
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function init() {
  const manifest = await loadJson(MANIFEST);
  const root = manifest.artifacts;
  const [state, hiring, competitor, traces, email, sms, hubspot, calcom] = await Promise.all([
    loadJson(root.state),
    loadJson(root.hiring_signal),
    loadJson(root.competitor_gap),
    loadText(root.agent_traces),
    loadJson(root.email_outbound),
    loadJson(root.sms_confirmation),
    loadJson(root.hubspot),
    loadJson(root.calcom),
  ]);

  const traceEntries = lines(traces).filter((entry) => entry.lead_id === manifest.lead_id);

  const summary = document.getElementById("summary");
  summary.append(
    el("p", "kicker", "Summary"),
    el("h2", null, `${state.lead.company_name}`),
    el("p", null, `Lead ${manifest.lead_id} reached ${state.conversation.stage} with booking status ${state.conversation.booking_status}.`),
    el("p", "subtle", `Trace steps: ${traceEntries.length}`),
  );

  const signals = document.getElementById("signals");
  signals.append(el("p", "kicker", "Signals"), el("h2", null, "Enrichment output"));
  [hiring.funding_signal, hiring.job_post_signal, hiring.layoff_signal, hiring.leadership_change_signal].forEach((signal) => {
    signals.append(el("div", "row", `${signal.name}: ${signal.value}`));
  });

  const ops = document.getElementById("ops");
  ops.append(el("p", "kicker", "Operations"), el("h2", null, "Writes and handoffs"));
  [
    `Email: ${email.status} via ${email.provider}`,
    `SMS: ${sms.status} via ${sms.provider}`,
    `HubSpot: ${hubspot.status}`,
    `Cal.com: ${calcom.booking_url}`,
    `Recommended hook: ${competitor.recommended_hook}`,
  ].forEach((item) => ops.append(el("div", "row", item)));

  const tracePanel = document.getElementById("traces");
  tracePanel.append(el("p", "kicker", "Traces"), el("h2", null, "Latest step log"));
  traceEntries.slice(-8).forEach((entry) => {
    tracePanel.append(el("div", "row", `${entry.step_name} · ${entry.latency_ms} ms · ${entry.status}`));
  });
}

init().catch((error) => {
  document.body.insertAdjacentHTML("beforeend", `<pre class="error">${error.message}</pre>`);
});
