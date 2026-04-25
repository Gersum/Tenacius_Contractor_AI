const MANIFEST = "../artifacts/runtime/current-run.json";
const OPERATOR_ORIGIN = "http://127.0.0.1:8000";

function apiPath(path) {
  if (window.location.protocol === "file:") {
    return `${OPERATOR_ORIGIN}${path}`;
  }
  return path;
}

const state = {
  manifest: null,
  artifacts: {},
  traces: [],
  apiOnline: false,
};

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

async function postJson(path, payload = {}) {
  const response = await fetch(apiPath(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  if (!response.ok || body.status === "error") {
    throw new Error(body.message || `Request failed: ${path}`);
  }
  return body;
}

function lines(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function setBusy(isBusy, label = "") {
  document.querySelectorAll("button").forEach((button) => {
    button.disabled = isBusy || (!state.apiOnline && button.id !== "refresh-data");
  });
  const lastRun = document.getElementById("last-run");
  if (label) lastRun.textContent = label;
}

function readLeadForm() {
  const data = new FormData(document.getElementById("lead-form"));
  return {
    company_name: data.get("company_name"),
    domain: data.get("domain"),
    synthetic_contact_name: data.get("synthetic_contact_name"),
    synthetic_contact_email: data.get("synthetic_contact_email"),
    synthetic_contact_phone: data.get("synthetic_contact_phone"),
  };
}

async function checkApi() {
  const badge = document.getElementById("api-status");
  try {
    await loadJson(apiPath("/api/health"));
    state.apiOnline = true;
    badge.textContent = window.location.protocol === "file:" ? "Open served URL for actions" : "Operator API online";
    badge.className = "status-dot online";
  } catch {
    state.apiOnline = false;
    badge.textContent = "Static mode only - open http://127.0.0.1:8000/visualization/";
    badge.className = "status-dot offline";
  }
  setBusy(false);
}

async function loadDashboard() {
  const manifest = await loadJson(MANIFEST);
  const root = manifest.artifacts;
  const [stateJson, hiring, competitor, traces, email, sms, hubspot, calcom, scoreLog] = await Promise.all([
    loadJson(root.state),
    loadJson(root.hiring_signal),
    loadJson(root.competitor_gap),
    loadText(root.agent_traces),
    loadJson(root.email_outbound),
    loadJson(root.sms_confirmation),
    loadJson(root.hubspot),
    loadJson(root.calcom),
    loadJson(root.eval_score_log),
  ]);

  state.manifest = manifest;
  state.artifacts = { stateJson, hiring, competitor, email, sms, hubspot, calcom, scoreLog };
  state.traces = lines(traces).filter((entry) => entry.lead_id === manifest.lead_id);

  renderSummary();
  renderSignals();
  renderOperations();
  renderTraces();
  renderWorkflow();
  renderArtifactPicker();
}

function renderSummary() {
  const { manifest, artifacts, traces } = state;
  const panel = document.getElementById("summary");
  clear(panel);
  const devScore = artifacts.scoreLog.find((entry) => entry.run_label === "dev_baseline");
  panel.append(
    el("p", "kicker", "Current Run"),
    el("h2", null, artifacts.stateJson.lead.company_name),
    el(
      "p",
      null,
      `Lead ${manifest.lead_id} reached ${artifacts.stateJson.conversation.stage} with booking status ${artifacts.stateJson.conversation.booking_status}.`,
    ),
    metricRow("Trace steps", traces.length),
    metricRow("Tau pass@1", `${devScore.pass_at_1} (${devScore.pass_at_1_ci_95.join(" - ")})`),
    metricRow("Avg tau cost", `$${devScore.avg_agent_cost}`),
  );
}

function renderSignals() {
  const { hiring } = state.artifacts;
  const panel = document.getElementById("signals");
  clear(panel);
  panel.append(el("p", "kicker", "Signals"), el("h2", null, "Enrichment output"));
  [hiring.funding_signal, hiring.job_post_signal, hiring.layoff_signal, hiring.leadership_change_signal].forEach(
    (signal) => {
      panel.append(signalRow(signal.name, signal.value, signal.confidence));
    },
  );
  panel.append(metricRow("AI maturity", `${hiring.ai_maturity_score}/3`));
}

function renderOperations() {
  const { manifest, artifacts } = state;
  const panel = document.getElementById("ops");
  clear(panel);
  const calcomBooking = artifacts.calcom.booking || artifacts.calcom;
  panel.append(el("p", "kicker", "Operations"), el("h2", null, "Writes and handoffs"));
  [
    ["Email", `${artifacts.email.status} via ${artifacts.email.provider}`],
    ["SMS", `${artifacts.sms.status} via ${artifacts.sms.provider}`],
    ["HubSpot", `${artifacts.hubspot.status} with enrichment timestamp`],
    ["Cal.com", `${calcomBooking.status || "unknown"} via ${calcomBooking.mode || "unknown"} at ${calcomBooking.booking_url}`],
    ["Discovery brief", manifest.artifacts.discovery_context],
    ["Evidence graph", manifest.artifacts.evidence_graph],
  ].forEach(([label, value]) => panel.append(signalRow(label, value, "ok")));
}

function renderTraces() {
  const panel = document.getElementById("traces");
  clear(panel);
  panel.append(el("p", "kicker", "Traces"), el("h2", null, "Latest step log"));
  state.traces.slice(-9).forEach((entry) => {
    const row = el("div", `trace-row ${entry.status}`, "");
    row.append(el("span", null, entry.step_name), el("strong", null, `${entry.latency_ms} ms`));
    panel.append(row);
  });
}

function renderWorkflow() {
  const workflow = document.getElementById("workflow");
  clear(workflow);
  const completed = new Set(state.traces.map((trace) => trace.step_name));
  [
    ["Enrich", "build_hiring_signal_brief"],
    ["Email", "send_email"],
    ["Reply", "receive_reply"],
    ["Qualify", "qualify_reply"],
    ["Book", "book_calcom_meeting"],
    ["SMS warm follow-up", "send_sms_schedule_confirmation"],
    ["HubSpot", "sync_hubspot_record"],
  ].forEach(([label, step], index) => {
    const item = el("div", completed.has(step) ? "workflow-step done" : "workflow-step", "");
    item.append(el("span", null, String(index + 1)), el("p", null, label));
    workflow.append(item);
  });
}

function renderArtifactPicker() {
  const picker = document.getElementById("artifact-select");
  clear(picker);
  const options = Object.entries(state.manifest.artifacts).filter(([, path]) => path);
  options.forEach(([key, path]) => {
    const option = el("option", null, key.replaceAll("_", " "));
    option.value = path;
    picker.append(option);
  });
  picker.onchange = () => renderArtifact(picker.value);
  renderArtifact(picker.value);
}

async function renderArtifact(path) {
  const viewer = document.getElementById("artifact-viewer");
  viewer.textContent = "Loading artifact...";
  try {
    const text = await loadText(path);
    viewer.textContent = tryPrettyJson(text);
  } catch (error) {
    viewer.textContent = error.message;
  }
}

function tryPrettyJson(text) {
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
}

function signalRow(label, value, confidence) {
  const row = el("div", "row split", "");
  const copy = el("div", null, "");
  copy.append(el("strong", null, label), el("p", null, value));
  row.append(copy, el("span", "chip", confidence));
  return row;
}

function metricRow(label, value) {
  const row = el("div", "metric", "");
  row.append(el("span", null, label), el("strong", null, String(value)));
  return row;
}

async function runPipeline() {
  setBusy(true, "Running full pipeline...");
  try {
    const result = await postJson("/api/run", { lead: readLeadForm() });
    document.getElementById("last-run").textContent = `Created ${result.result.lead_id}`;
    await loadDashboard();
  } catch (error) {
    document.getElementById("last-run").textContent = error.message;
  } finally {
    setBusy(false);
  }
}

async function recomputeEval() {
  setBusy(true, "Recomputing tau score...");
  try {
    const result = await postJson("/api/recompute-eval");
    document.getElementById("last-run").textContent = `Score updated: ${result.summaries[0].pass_at_1} pass@1`;
    await loadDashboard();
  } catch (error) {
    document.getElementById("last-run").textContent = error.message;
  } finally {
    setBusy(false);
  }
}

document.getElementById("run-pipeline").addEventListener("click", runPipeline);
document.getElementById("recompute-eval").addEventListener("click", recomputeEval);
document.getElementById("refresh-data").addEventListener("click", async () => {
  document.getElementById("last-run").textContent = "Refreshing evidence...";
  await loadDashboard();
  document.getElementById("last-run").textContent = "Evidence refreshed";
});

checkApi()
  .then(loadDashboard)
  .catch((error) => {
    document.body.insertAdjacentHTML("beforeend", `<pre class="error">${error.message}</pre>`);
  });
