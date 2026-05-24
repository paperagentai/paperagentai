// ── PaperAgent — Frontend for GitHub Pages ──────────────────────────────────
// Connects to a separately-running Flask backend.

const STEP_DEFS = [
  { key: "1",  label: "Step 1",   title: "Literature Review",            log: "01_literature.md" },
  { key: "2",  label: "Step 2",   title: "Research Questions",            log: "02_research_questions.md" },
  { key: "3",  label: "Step 3",   title: "Experiment Design",             log: "03_experiment_design.md" },
  { key: "4a", label: "Step 4a",  title: "Code Gen — run_experiments.py",  log: "04a_code.md" },
  { key: "4b", label: "Step 4b",  title: "Code Gen — prompts.py",          log: "04b_code.md" },
  { key: "5a", label: "Step 5a",  title: "Paper — Related Work + Intro",   log: "05a_paper.md" },
  { key: "5b", label: "Step 5b",  title: "Paper — Methodology",            log: "05b_paper.md" },
  { key: "5c", label: "Step 5c",  title: "Paper — Results",                log: "05c_paper.md" },
  { key: "5d", label: "Step 5d",  title: "Paper — Discussion + Conclusion",log: "05d_paper.md" },
  { key: "5e", label: "Step 5e",  title: "Paper — Review",                 log: "05e_modifications.md" },
];

// ── Backend URL (persisted in localStorage) ────────────────────────────────
function getBackendUrl() {
  return localStorage.getItem("paperagent_backend_url") || "http://localhost:5000";
}
function setBackendUrl(url) {
  localStorage.setItem("paperagent_backend_url", url.replace(/\/+$/, ""));
}

// ── DOM helpers ────────────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

let eventSource = null;
let currentRunningStep = null;

// ── Navigation ─────────────────────────────────────────────────────────────
document.querySelectorAll(".nav-link").forEach(link => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    switchTab(link.dataset.tab);
  });
});

function switchTab(tab) {
  document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  $(`.nav-link[data-tab="${tab}"]`).classList.add("active");
  $(`#tab-${tab}`).classList.add("active");
  if (tab === "pipeline") buildStepGrid();
  if (tab === "logs") loadLogs();
}

// ── Config ─────────────────────────────────────────────────────────────────
async function loadConfig() {
  // Restore backend URL from localStorage
  $("#backend-url").value = getBackendUrl();

  const backend = getBackendUrl();
  try {
    const res = await fetch(`${backend}/api/config`);
    if (!res.ok) throw new Error("Backend not reachable");
    const cfg = await res.json();
    $("#research-question").value = cfg.research_question || "";
    $("#research-context").value = cfg.research_context || "";
    $("#recent-papers").value = cfg.recent_papers || "";
    $("#feedback").value = cfg.feedback || "";
    $("#api-key").value = cfg.api_key || "";
    $("#base-url").value = cfg.base_url || "https://api.deepseek.com";
    $("#model").value = cfg.model || "deepseek-v4-pro";
    $("#config-error-msg").textContent = "";
  } catch (err) {
    console.log("Backend not reachable — showing empty config. Start the backend and Save to sync.");
    $("#config-error-msg").textContent = "⚠ Backend not reachable. Start it, then click Save.";
  }
}

$("#backend-url").addEventListener("change", () => {
  setBackendUrl($("#backend-url").value);
});

$("#btn-save-config").addEventListener("click", async () => {
  const backend = getBackendUrl();
  const payload = {
    research_question: $("#research-question").value,
    research_context: $("#research-context").value,
    recent_papers: $("#recent-papers").value,
    feedback: $("#feedback").value,
    api_key: $("#api-key").value,
    base_url: $("#base-url").value,
    model: $("#model").value,
  };

  try {
    const res = await fetch(`${backend}/api/config`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Save failed");

    const msg = $("#config-saved-msg");
    msg.textContent = "✓ Saved to backend!";
    msg.classList.add("show");
    setTimeout(() => msg.classList.remove("show"), 2500);
    $("#config-error-msg").textContent = "";
  } catch (err) {
    $("#config-error-msg").textContent = "✕ Failed to save — is the backend running?";
  }
});

// ── Pipeline ───────────────────────────────────────────────────────────────
function buildStepGrid() {
  const grid = $("#step-grid");
  grid.innerHTML = STEP_DEFS.map(s => `
    <div class="step-card" id="step-card-${s.key}">
      <div class="step-label">${s.label}</div>
      <div class="step-title">${s.title}</div>
      <div class="step-log">→ ${s.log}</div>
      <div class="step-actions">
        <button class="btn btn-sm btn-run" data-step="${s.key}">▶ Run</button>
        <button class="btn btn-sm btn-view-log" data-step="${s.key}" data-log="${s.log}">📄 View</button>
      </div>
      <div class="step-status" id="step-status-${s.key}"></div>
    </div>
  `).join("");

  grid.querySelectorAll(".btn-run").forEach(btn => {
    btn.addEventListener("click", () => runStep(btn.dataset.step));
  });
  grid.querySelectorAll(".btn-view-log").forEach(btn => {
    btn.addEventListener("click", () => viewStepLog(btn.dataset.log, btn.dataset.step));
  });
}

async function runStep(stepKey) {
  if (eventSource) {
    alert("A pipeline step is already running. Wait for it to finish or cancel.");
    return;
  }

  const apiKey = $("#api-key").value;
  const baseUrl = $("#base-url").value;
  const model = $("#model").value;
  const backend = getBackendUrl();

  if (!apiKey) {
    alert("Please set your LLM API key in the Config tab first.");
    return;
  }

  resetStepStatuses();
  $("#output-content").textContent = "";
  $("#output-step-label").textContent = `— Step ${stepKey}`;
  currentRunningStep = stepKey;

  setRunning(true);
  markStepRunning(stepKey);
  updateStatus("running", `Running Step ${stepKey}...`);

  try {
    const res = await fetch(`${backend}/api/run/${stepKey}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: apiKey, base_url: baseUrl, model: model }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Failed to start pipeline");
    }

    startSSE();
  } catch (err) {
    $("#output-content").textContent = `ERROR: ${err.message}\n\nIs the backend running at ${backend}?`;
    setRunning(false);
    markStepError(stepKey);
    updateStatus("error", err.message);
  }
}

$("#btn-run-all").addEventListener("click", async () => {
  if (eventSource) {
    alert("A pipeline step is already running. Wait for it to finish or cancel.");
    return;
  }

  const apiKey = $("#api-key").value;
  const backend = getBackendUrl();

  if (!apiKey) {
    alert("Please set your LLM API key in the Config tab first.");
    return;
  }

  resetStepStatuses();
  $("#output-content").textContent = "";
  $("#output-step-label").textContent = "— All Steps";
  currentRunningStep = null;

  setRunning(true);
  updateStatus("running", "Running all steps...");

  try {
    const res = await fetch(`${backend}/api/run/all`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        api_key: apiKey,
        base_url: $("#base-url").value,
        model: $("#model").value,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Failed to start pipeline");
    }

    startSSE();
  } catch (err) {
    $("#output-content").textContent = `ERROR: ${err.message}\n\nIs the backend running at ${backend}?`;
    setRunning(false);
    updateStatus("error", err.message);
  }
});

function startSSE() {
  if (eventSource) eventSource.close();
  const backend = getBackendUrl();

  eventSource = new EventSource(`${backend}/api/stream`);

  eventSource.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    switch (msg.type) {
      case "status":
        $("#output-content").textContent += `\n── ${msg.data} ──\n`;
        $("#output-content").scrollTop = $("#output-content").scrollHeight;
        break;

      case "token":
        $("#output-content").textContent += msg.data;
        $("#output-content").scrollTop = $("#output-content").scrollHeight;
        break;

      case "step_change":
        if (currentRunningStep) markStepDone(currentRunningStep);
        currentRunningStep = msg.data;
        markStepRunning(msg.data);
        $("#output-step-label").textContent = `— Step ${msg.data}`;
        break;

      case "error":
        $("#output-content").textContent += `\n❌ ERROR: ${msg.data}\n`;
        $("#output-content").scrollTop = $("#output-content").scrollHeight;
        if (currentRunningStep) markStepError(currentRunningStep);
        updateStatus("error", msg.data);
        break;

      case "done":
        if (currentRunningStep) markStepDone(currentRunningStep);
        setRunning(false);
        updateStatus("idle", "Done ✓");
        closeSSE();
        break;

      case "heartbeat":
        break;
    }
  };

  eventSource.onerror = () => {
    if (eventSource) {
      closeSSE();
      setRunning(false);
      updateStatus("error", "Connection lost — is the backend still running?");
    }
  };
}

function closeSSE() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  currentRunningStep = null;
}

$("#btn-cancel").addEventListener("click", async () => {
  await fetch(`${getBackendUrl()}/api/cancel`, { method: "POST" });
  closeSSE();
  setRunning(false);
  if (currentRunningStep) markStepError(currentRunningStep);
  updateStatus("idle", "Cancelled");
  currentRunningStep = null;
});

$("#btn-clear-output").addEventListener("click", () => {
  $("#output-content").textContent = "";
  $("#output-step-label").textContent = "";
});

// ── UI state helpers ───────────────────────────────────────────────────────
function setRunning(running) {
  $("#btn-run-all").disabled = running;
  $("#btn-cancel").disabled = !running;
  document.querySelectorAll(".btn-run").forEach(b => b.disabled = running);
}

function markStepRunning(key) {
  const card = $(`#step-card-${key}`);
  if (card) card.classList.add("running");
  const status = $(`#step-status-${key}`);
  if (status) { status.textContent = "⏳ Running..."; status.className = "step-status step-status-running"; }
}

function markStepDone(key) {
  const card = $(`#step-card-${key}`);
  if (card) { card.classList.remove("running"); card.classList.add("done"); }
  const status = $(`#step-status-${key}`);
  if (status) { status.textContent = "✓ Done"; status.className = "step-status step-status-done"; }
}

function markStepError(key) {
  const card = $(`#step-card-${key}`);
  if (card) { card.classList.remove("running"); card.classList.add("error"); }
  const status = $(`#step-status-${key}`);
  if (status) { status.textContent = "✕ Error"; status.className = "step-status step-status-error"; }
}

function resetStepStatuses() {
  STEP_DEFS.forEach(s => {
    const card = $(`#step-card-${s.key}`);
    if (card) card.classList.remove("running", "done", "error");
    const status = $(`#step-status-${s.key}`);
    if (status) { status.textContent = ""; status.className = "step-status"; }
  });
}

function updateStatus(state, text) {
  const indicator = $("#status-indicator");
  indicator.textContent = (state === "running" ? "● " : "● ") + text;
  indicator.className = state === "running" ? "status-running"
    : state === "error" ? "status-error"
    : "status-idle";
}

async function viewStepLog(logFile, stepKey) {
  const backend = getBackendUrl();
  try {
    const res = await fetch(`${backend}/api/logs/${logFile}`);
    if (!res.ok) {
      $("#output-content").textContent = `Log not found: ${logFile}\n(run the step first, and make sure the backend is running at ${backend})`;
      return;
    }
    const data = await res.json();
    $("#output-content").textContent = data.content || "(empty)";
    $("#output-step-label").textContent = `— ${logFile}`;
    const card = $(`#step-card-${stepKey}`);
    if (card) {
      card.style.boxShadow = "0 0 0 2px var(--accent)";
      setTimeout(() => { card.style.boxShadow = ""; }, 1500);
    }
  } catch (err) {
    $("#output-content").textContent = `ERROR: ${err.message}\n\nIs the backend running at ${backend}?`;
  }
}

// ── Logs Tab ───────────────────────────────────────────────────────────────
async function loadLogs() {
  const backend = getBackendUrl();
  const list = $("#log-list");

  try {
    const res = await fetch(`${backend}/api/logs`);
    if (!res.ok) throw new Error("Failed to fetch logs");

    const logs = await res.json();

    if (logs.length === 0) {
      list.innerHTML = '<p style="color: var(--text-muted); padding: 12px;">No log files yet. Run some pipeline steps first.</p>';
      return;
    }

    list.innerHTML = logs.map(l => `
      <div class="log-item">
        <span class="log-name">📄 ${l.name}</span>
        <span class="log-meta">${formatSize(l.size)} — ${formatDate(l.mtime)}</span>
        <div class="log-actions">
          <button class="btn btn-sm btn-view-full" data-log="${l.name}">View</button>
          <button class="btn btn-sm btn-delete-log" data-log="${l.name}">🗑</button>
        </div>
      </div>
    `).join("");

    list.querySelectorAll(".btn-view-full").forEach(btn => {
      btn.addEventListener("click", () => viewFullLog(btn.dataset.log));
    });
    list.querySelectorAll(".btn-delete-log").forEach(btn => {
      btn.addEventListener("click", async () => {
        if (!confirm(`Delete ${btn.dataset.log}?`)) return;
        await fetch(`${backend}/api/logs/${btn.dataset.log}`, { method: "DELETE" });
        loadLogs();
      });
    });
  } catch (err) {
    list.innerHTML = `<p style="color: var(--red); padding: 12px;">⚠ Cannot reach backend at ${backend}. Make sure it's running.</p>`;
  }
}

async function viewFullLog(filename) {
  const backend = getBackendUrl();
  try {
    const res = await fetch(`${backend}/api/logs/${filename}`);
    const data = await res.json();
    $("#log-viewer-title").textContent = `📄 ${filename}`;
    $("#log-viewer-content").textContent = data.content || "(empty)";
    $("#log-viewer").style.display = "block";
    $("#log-viewer").scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    alert(`Failed to load log. Is the backend running at ${backend}?`);
  }
}

$("#btn-close-log").addEventListener("click", () => {
  $("#log-viewer").style.display = "none";
});

$("#btn-refresh-logs").addEventListener("click", loadLogs);

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function formatDate(iso) {
  return new Date(iso).toLocaleString();
}

// ── Init ───────────────────────────────────────────────────────────────────
loadConfig();
buildStepGrid();

// Check backend status on load
(async () => {
  try {
    const res = await fetch(`${getBackendUrl()}/api/status`);
    const status = await res.json();
    if (status.running) {
      setRunning(true);
      updateStatus("running", `Running Step ${status.current_step || "?"}...`);
      startSSE(); // reconnect to existing SSE stream
    }
  } catch (e) { /* backend not running — that's ok */ }
})();
