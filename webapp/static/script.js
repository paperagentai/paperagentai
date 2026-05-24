// ── Research Pipeline — Frontend ────────────────────────────────────────────

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

let eventSource = null;
let currentRunningStep = null;

// ── DOM refs ────────────────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ── Navigation ──────────────────────────────────────────────────────────────
document.querySelectorAll(".nav-link").forEach(link => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const tab = link.dataset.tab;
    switchTab(tab);
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

// ── Config ──────────────────────────────────────────────────────────────────
async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    const cfg = await res.json();
    $("#research-question").value = cfg.research_question || "";
    $("#research-context").value = cfg.research_context || "";
    $("#recent-papers").value = cfg.recent_papers || "";
    $("#feedback").value = cfg.feedback || "";
    $("#api-key").value = cfg.api_key || "";
    $("#base-url").value = cfg.base_url || "https://api.deepseek.com";
    $("#model").value = cfg.model || "deepseek-v4-pro";
  } catch (err) {
    console.error("Failed to load config:", err);
  }
}

$("#btn-save-config").addEventListener("click", async () => {
  const payload = {
    research_question: $("#research-question").value,
    research_context: $("#research-context").value,
    recent_papers: $("#recent-papers").value,
    feedback: $("#feedback").value,
    api_key: $("#api-key").value,
    base_url: $("#base-url").value,
    model: $("#model").value,
  };

  const res = await fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (res.ok) {
    const msg = $("#config-saved-msg");
    msg.textContent = "✓ Saved!";
    msg.classList.add("show");
    setTimeout(() => msg.classList.remove("show"), 2000);
  }
});

// ── Pipeline ────────────────────────────────────────────────────────────────
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

  // Bind run buttons
  grid.querySelectorAll(".btn-run").forEach(btn => {
    btn.addEventListener("click", () => runStep(btn.dataset.step));
  });

  // Bind view log buttons
  grid.querySelectorAll(".btn-view-log").forEach(btn => {
    btn.addEventListener("click", () => viewStepLog(btn.dataset.log, btn.dataset.step));
  });
}

async function runStep(stepKey) {
  if (eventSource) {
    alert("A pipeline step is already running. Wait for it to finish or cancel it.");
    return;
  }

  const apiKey = $("#api-key").value;
  const baseUrl = $("#base-url").value;
  const model = $("#model").value;

  if (!apiKey) {
    alert("Please set your API key in the Config tab first.");
    return;
  }

  // Reset UI
  resetStepStatuses();
  $("#output-content").textContent = "";
  $("#output-step-label").textContent = `— Step ${stepKey}`;
  currentRunningStep = stepKey;

  setRunning(true);
  markStepRunning(stepKey);
  updateStatus("running", `Running Step ${stepKey}...`);

  try {
    const res = await fetch(`/api/run/${stepKey}`, {
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
    $("#output-content").textContent = `ERROR: ${err.message}`;
    setRunning(false);
    markStepError(stepKey);
    updateStatus("error", err.message);
  }
}

$("#btn-run-all").addEventListener("click", async () => {
  if (eventSource) {
    alert("A pipeline step is already running. Wait for it to finish or cancel it.");
    return;
  }

  const apiKey = $("#api-key").value;
  if (!apiKey) {
    alert("Please set your API key in the Config tab first.");
    return;
  }

  // Reset
  resetStepStatuses();
  $("#output-content").textContent = "";
  $("#output-step-label").textContent = "— All Steps";
  currentRunningStep = null;

  setRunning(true);
  updateStatus("running", "Running all steps...");

  try {
    const res = await fetch("/api/run/all", {
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
    $("#output-content").textContent = `ERROR: ${err.message}`;
    setRunning(false);
    updateStatus("error", err.message);
  }
});

function startSSE() {
  if (eventSource) eventSource.close();

  eventSource = new EventSource("/api/stream");

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
        // no-op
        break;
    }
  };

  eventSource.onerror = () => {
    if (eventSource) {
      closeSSE();
      setRunning(false);
      updateStatus("error", "Connection lost");
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
  await fetch("/api/cancel", { method: "POST" });
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

// ── UI state helpers ────────────────────────────────────────────────────────
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
  indicator.textContent = state === "running" ? "● " + text : "● " + text;
  indicator.className = state === "running" ? "status-running"
    : state === "error" ? "status-error"
    : "status-idle";
}

async function viewStepLog(logFile, stepKey) {
  try {
    const res = await fetch(`/api/logs/${logFile}`);
    if (!res.ok) {
      $("#output-content").textContent = `Log not found: ${logFile} (run the step first)`;
      return;
    }
    const data = await res.json();
    $("#output-content").textContent = data.content || "(empty)";
    $("#output-step-label").textContent = `— ${logFile}`;
    // Highlight the step card briefly
    const card = $(`#step-card-${stepKey}`);
    if (card) {
      card.style.boxShadow = "0 0 0 2px var(--accent)";
      setTimeout(() => { card.style.boxShadow = ""; }, 1500);
    }
  } catch (err) {
    console.error(err);
  }
}

// ── Logs Tab ────────────────────────────────────────────────────────────────
async function loadLogs() {
  try {
    const res = await fetch("/api/logs");
    const logs = await res.json();

    const list = $("#log-list");
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

    // Bind view buttons
    list.querySelectorAll(".btn-view-full").forEach(btn => {
      btn.addEventListener("click", () => viewFullLog(btn.dataset.log));
    });

    // Bind delete buttons
    list.querySelectorAll(".btn-delete-log").forEach(btn => {
      btn.addEventListener("click", async () => {
        if (!confirm(`Delete ${btn.dataset.log}?`)) return;
        await fetch(`/api/logs/${btn.dataset.log}`, { method: "DELETE" });
        loadLogs();
      });
    });
  } catch (err) {
    console.error(err);
  }
}

async function viewFullLog(filename) {
  try {
    const res = await fetch(`/api/logs/${filename}`);
    const data = await res.json();
    $("#log-viewer-title").textContent = `📄 ${filename}`;
    $("#log-viewer-content").textContent = data.content || "(empty)";
    $("#log-viewer").style.display = "block";
    $("#log-viewer").scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error(err);
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
  const d = new Date(iso);
  return d.toLocaleString();
}

// ── Init ────────────────────────────────────────────────────────────────────
loadConfig();
buildStepGrid();

// Check pipeline status on load
(async () => {
  try {
    const res = await fetch("/api/status");
    const status = await res.json();
    if (status.running) {
      setRunning(true);
      updateStatus("running", `Running Step ${status.current_step || "?"}...`);
    }
  } catch (e) { /* ignore */ }
})();
