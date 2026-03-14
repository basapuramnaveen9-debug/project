const codeInput = document.getElementById("codeInput");
const optimizeBtn = document.getElementById("optimizeBtn");
const sampleBtn = document.getElementById("sampleBtn");
const stopBtn = document.getElementById("stopBtn");
const executionControls = document.getElementById("executionControls");
const statusEl = document.getElementById("status");

const optimizedOut = document.getElementById("optimizedOut");
const aiOut = document.getElementById("aiOut");
const algoOut = document.getElementById("algoOut");
const complexityOut = document.getElementById("complexityOut");
const spaceComplexityOut = document.getElementById("spaceComplexityOut");
const loopsOut = document.getElementById("loopsOut");
const runtimeOut = document.getElementById("runtimeOut");
const linesBeforeOut = document.getElementById("linesBeforeOut");
const linesAfterOut = document.getElementById("linesAfterOut");
const executionOut = document.getElementById("executionOut");

let activeSessionId = null;
let executionCursor = 0;
let pollTimer = null;
let executionBuffer = "";
let pendingInput = "";
let sendingInput = false;

function renderList(node, items) {
  node.innerHTML = "";
  if (!Array.isArray(items) || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No data";
    node.appendChild(li);
    return;
  }

  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    node.appendChild(li);
  }
}

function clearAnalysis() {
  optimizedOut.textContent = "-";
  aiOut.innerHTML = "";
  algoOut.innerHTML = "";
  complexityOut.textContent = "-";
  spaceComplexityOut.textContent = "-";
  loopsOut.textContent = "-";
  runtimeOut.textContent = "-";
  linesBeforeOut.textContent = "-";
  linesAfterOut.textContent = "-";
}

function moveCaretToEnd() {
  const end = executionOut.value.length;
  executionOut.setSelectionRange(end, end);
}

function renderExecution() {
  executionOut.value = `${executionBuffer}${pendingInput}`;
  executionOut.scrollTop = executionOut.scrollHeight;
  moveCaretToEnd();
}

function setExecutionControls(active) {
  executionControls.classList.toggle("hidden", !active);
  executionOut.readOnly = !active;

  if (!active) {
    pendingInput = "";
    renderExecution();
    return;
  }

  executionOut.focus();
  moveCaretToEnd();
}

function stopPolling() {
  if (pollTimer) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
}

async function stopActiveSession(silent = false) {
  if (!activeSessionId) {
    return;
  }

  const sessionId = activeSessionId;
  activeSessionId = null;
  stopPolling();
  setExecutionControls(false);

  try {
    await fetch(`/execute/${sessionId}/stop`, { method: "POST" });
  } catch (err) {
    if (!silent) {
      statusEl.textContent = `Error: ${err.message}`;
    }
  }
}

function appendExecution(text) {
  if (!text) {
    return;
  }

  executionBuffer += text;
  renderExecution();
}

function isExecutionError(output) {
  if (!output) {
    return false;
  }

  const text = String(output).toLowerCase();
  return [
    "error:",
    "undefined reference",
    "compilation failed",
    "unable to run compiled program",
    "runtime timed out",
    "compilation timed out",
    "compiler not found",
    "blocked the generated executable",
    "program exited with code",
  ].some((marker) => text.includes(marker));
}

async function sendConsoleInput() {
  if (!activeSessionId || sendingInput) {
    return;
  }

  const inputText = pendingInput;
  sendingInput = true;

  try {
    const resp = await fetch(`/execute/${activeSessionId}/input`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input: inputText })
    });

    const data = await resp.json();
    if (!resp.ok || !data.ok) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    executionBuffer += `${inputText}\n`;
    pendingInput = "";
    renderExecution();
    statusEl.textContent = "Input sent to the running program.";
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
    renderExecution();
  } finally {
    sendingInput = false;
  }
}

async function pollExecution() {
  if (!activeSessionId) {
    return;
  }

  try {
    const resp = await fetch(`/execute/${activeSessionId}/poll?cursor=${executionCursor}`);
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }

    const data = await resp.json();
    appendExecution(data.output || "");
    executionCursor = data.cursor ?? executionCursor;

    if (data.finished) {
      const finalOutput = executionBuffer.trim();
      const exitCode = data.exit_code;
      activeSessionId = null;
      stopPolling();
      setExecutionControls(false);

      if (!finalOutput) {
        executionBuffer = "(Program produced no output)";
        renderExecution();
      }

      if (exitCode && exitCode !== 0) {
        clearAnalysis();
        statusEl.textContent = `Program exited with code ${exitCode}.`;
        return;
      }

      if (isExecutionError(finalOutput)) {
        clearAnalysis();
        statusEl.textContent = "Error found. Showing only compiler/runtime output.";
        return;
      }

      statusEl.textContent = "Done.";
      return;
    }

    pollTimer = setTimeout(pollExecution, 350);
  } catch (err) {
    activeSessionId = null;
    stopPolling();
    setExecutionControls(false);
    statusEl.textContent = `Error: ${err.message}`;
  }
}

sampleBtn.addEventListener("click", async () => {
  sampleBtn.disabled = true;
  statusEl.textContent = "Generating random sample...";

  try {
    const resp = await fetch("/sample");
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }

    const data = await resp.json();
    codeInput.value = data.code || "";
    statusEl.textContent = "Random sample loaded.";
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  } finally {
    sampleBtn.disabled = false;
  }
});

executionOut.addEventListener("keydown", async (event) => {
  if (!activeSessionId) {
    event.preventDefault();
    return;
  }

  const blockedKeys = ["ArrowLeft", "ArrowUp", "Home", "PageUp"];
  if (blockedKeys.includes(event.key)) {
    event.preventDefault();
    moveCaretToEnd();
    return;
  }

  if (event.key === "Enter") {
    event.preventDefault();
    await sendConsoleInput();
    return;
  }

  setTimeout(moveCaretToEnd, 0);
});

executionOut.addEventListener("input", () => {
  if (!activeSessionId) {
    renderExecution();
    return;
  }

  if (!executionOut.value.startsWith(executionBuffer)) {
    renderExecution();
    return;
  }

  pendingInput = executionOut.value.slice(executionBuffer.length);
  moveCaretToEnd();
});

executionOut.addEventListener("click", () => {
  if (activeSessionId) {
    moveCaretToEnd();
  }
});

executionOut.addEventListener("focus", () => {
  if (activeSessionId) {
    moveCaretToEnd();
  }
});

stopBtn.addEventListener("click", async () => {
  await stopActiveSession();
  executionBuffer += executionBuffer ? "\n\n[Program stopped by user]" : "[Program stopped by user]";
  renderExecution();
  statusEl.textContent = "Program stopped.";
});

optimizeBtn.addEventListener("click", async () => {
  const code = codeInput.value.trim();
  if (!code) {
    statusEl.textContent = "Enter code first.";
    return;
  }

  optimizeBtn.disabled = true;
  sampleBtn.disabled = true;
  statusEl.textContent = "Running analysis...";

  await stopActiveSession(true);
  executionCursor = 0;
  executionBuffer = "";
  pendingInput = "";
  renderExecution();

  try {
    const analysisResp = await fetch("/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code })
    });

    if (!analysisResp.ok) {
      throw new Error(`HTTP ${analysisResp.status}`);
    }

    const data = await analysisResp.json();
    optimizedOut.textContent = data.optimized || "";
    renderList(aiOut, data.ai || []);
    renderList(algoOut, data.algorithm || []);
    complexityOut.textContent = data.complexity || "-";
    spaceComplexityOut.textContent = data.space_complexity || "-";
    loopsOut.textContent = data.loops ?? "-";
    runtimeOut.textContent = data.runtime || "-";
    linesBeforeOut.textContent = data.lines_before ?? "-";
    linesAfterOut.textContent = data.lines_after ?? "-";

    const executeResp = await fetch("/execute/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code })
    });

    const executeData = await executeResp.json();
    if (!executeResp.ok || !executeData.ok) {
      executionBuffer = executeData.error || "Failed to start program execution.";
      renderExecution();
      clearAnalysis();
      statusEl.textContent = "Error found. Showing only compiler/runtime output.";
      return;
    }

    activeSessionId = executeData.session_id;
    setExecutionControls(true);
    statusEl.textContent = "Program started. Type in the same console and press Enter if input is needed.";
    pollExecution();
  } catch (err) {
    clearAnalysis();
    statusEl.textContent = `Error: ${err.message}`;
    executionBuffer = "Failed to retrieve compiler output.";
    renderExecution();
  } finally {
    optimizeBtn.disabled = false;
    sampleBtn.disabled = false;
  }
});

renderExecution();
