const STORAGE_KEY = "studio-ai-optimization-request";
const RETURN_TO_STUDIO_KEY = "studio-ai-optimization-return";
const languageLabels = {
  c: "C",
  cpp: "C++",
  java: "Java",
  python: "Python",
  javascript: "JavaScript",
  typescript: "TypeScript",
  go: "Go",
  rust: "Rust",
  csharp: "C#",
  php: "PHP",
  ruby: "Ruby",
  kotlin: "Kotlin"
};

const backToStudioBtn = document.getElementById("backToStudioBtn");
const regenerateVariantsBtn = document.getElementById("regenerateVariantsBtn");
const variantCountInput = document.getElementById("variantCountInput");
const variantSourceMeta = document.getElementById("variantSourceMeta");
const sourceLineNumbers = document.getElementById("sourceLineNumbers");
const sourceCodeOut = document.getElementById("sourceCodeOut");
const variantSourcePanel = document.querySelector(".variant-source-panel");
const variantStatus = document.getElementById("variantStatus");
const variantEmptyState = document.getElementById("variantEmptyState");
const variantsGrid = document.getElementById("variantsGrid");
const variantFocusOverlay = document.getElementById("variantFocusOverlay");
const variantFocusKicker = document.getElementById("variantFocusKicker");
const variantFocusTitle = document.getElementById("variantFocusTitle");
const variantFocusSummary = document.getElementById("variantFocusSummary");
const variantFocusLineNumbers = document.getElementById("variantFocusLineNumbers");
const variantFocusCode = document.getElementById("variantFocusCode");
const variantFocusCodePanel = document.querySelector(".variant-focus-code-panel");
const variantFocusCopyBtn = document.getElementById("variantFocusCopyBtn");
const variantFocusCloseBtn = document.getElementById("variantFocusCloseBtn");

let activeRequest = readStoredRequest();
let focusedVariantCode = "";

function readStoredRequest() {
  try {
    return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null");
  } catch (_err) {
    return null;
  }
}

function getLanguageLabel(language) {
  return languageLabels[language] || String(language || "C").toUpperCase();
}

function getRequestedCount() {
  const value = Number.parseInt(variantCountInput?.value || "5", 10);
  return Number.isFinite(value) && value > 0 ? value : 5;
}

function buildLineNumbers(text) {
  const lineCount = Math.max(String(text ?? "").split("\n").length, 1);
  return Array.from({ length: lineCount }, (_, index) => index + 1).join("\n");
}

function syncLineNumberScroll(sourceNode, gutterNode) {
  if (!sourceNode || !gutterNode) {
    return;
  }

  gutterNode.scrollTop = sourceNode.scrollTop;
}

function setSourceCode(text) {
  const content = text || "";
  sourceCodeOut.textContent = content;
  sourceLineNumbers.textContent = buildLineNumbers(content);
}

function setStatus(message, isError = false) {
  variantStatus.textContent = message;
  variantStatus.classList.toggle("status-error", isError);
}

function setEmptyState(visible) {
  variantEmptyState.classList.toggle("hidden", !visible);
  variantsGrid.classList.toggle("hidden", visible);
}

function setOverlayCode(text) {
  const content = text || "";
  focusedVariantCode = content;
  variantFocusCode.textContent = content;
  variantFocusLineNumbers.textContent = buildLineNumbers(content);
  syncLineNumberScroll(variantFocusCode, variantFocusLineNumbers);
}

function getSourceFocusOptions() {
  return {
    kicker: "Source",
    title: "Original Program",
    summary: variantSourceMeta?.textContent || "",
    code: sourceCodeOut?.textContent || ""
  };
}

function openVariantFocus(options) {
  const {
    kicker = "Variant",
    title = "AI Optimized Variant",
    summary = "",
    code = ""
  } = options || {};

  variantFocusKicker.textContent = kicker;
  variantFocusTitle.textContent = title;
  variantFocusSummary.textContent = summary;
  variantFocusSummary.classList.toggle("hidden", !summary);
  setOverlayCode(code);
  variantFocusOverlay.classList.remove("hidden");
  variantFocusOverlay.setAttribute("aria-hidden", "false");
  document.body.classList.add("variant-focus-open");
}

function closeVariantFocus() {
  variantFocusOverlay.classList.add("hidden");
  variantFocusOverlay.setAttribute("aria-hidden", "true");
  document.body.classList.remove("variant-focus-open");
}

function createCopyButton(text) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "button-compact alt";
  button.textContent = "Copy Code";
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(text);
      const previous = button.textContent;
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.textContent = previous;
      }, 1200);
    } catch (_err) {
      button.textContent = "Copy Failed";
    }
  });
  return button;
}

function createExpandButton(options) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "icon-toggle-btn variant-code-toggle";
  button.setAttribute("aria-label", "Open full screen code");
  button.setAttribute("title", "Open full screen code");
  button.innerHTML = `
    <span class="icon-toggle-open" aria-hidden="true">
      <svg viewBox="0 0 24 24" focusable="false">
        <path d="M4 9V4h5M20 15v5h-5M15 4h5v5M9 20H4v-5" />
        <path d="M9 4L4 9M15 20l5-5M20 9l-5-5M4 15l5 5" />
      </svg>
    </span>
    <span class="icon-toggle-close" aria-hidden="true">
      <svg viewBox="0 0 24 24" focusable="false">
        <path d="M9 9H4V4M15 9h5V4M9 15H4v5M15 15h5v5" />
        <path d="M4 4l5 5M20 4l-5 5M4 20l5-5M20 20l-5-5" />
      </svg>
    </span>
  `;
  button.addEventListener("click", () => {
    openVariantFocus(typeof options === "function" ? options() : options);
  });
  return button;
}

function createScrollControlButton(direction, scroller) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "scroll-control-btn";
  button.setAttribute("aria-label", direction === "up" ? "Scroll up" : "Scroll down");
  button.setAttribute("title", direction === "up" ? "Scroll up" : "Scroll down");
  button.innerHTML = `
    <svg viewBox="0 0 24 24" focusable="false" aria-hidden="true">
      <path d="${direction === "up" ? "M6 14l6-6 6 6" : "M6 10l6 6 6-6"}" />
    </svg>
  `;
  button.addEventListener("click", () => {
    scroller.scrollBy({
      top: direction === "up" ? -180 : 180,
      behavior: "smooth"
    });
  });
  return button;
}

function createScrollControls(scroller, extraButton = null) {
  const controls = document.createElement("div");
  controls.className = "variant-scroll-controls";
  controls.appendChild(createScrollControlButton("up", scroller));
  controls.appendChild(createScrollControlButton("down", scroller));
  if (extraButton) {
    controls.appendChild(extraButton);
  }
  return controls;
}

function ensureStaticScrollControls() {
  if (variantSourcePanel && !variantSourcePanel.querySelector(".variant-scroll-controls")) {
    variantSourcePanel.appendChild(createScrollControls(
      sourceCodeOut,
      createExpandButton(getSourceFocusOptions)
    ));
  }

  if (variantFocusCodePanel && !variantFocusCodePanel.querySelector(".variant-scroll-controls")) {
    variantFocusCodePanel.appendChild(createScrollControls(variantFocusCode));
  }
}

function createVariantCard(variant, index) {
  const card = document.createElement("article");
  card.className = "block variant-card";

  const header = document.createElement("div");
  header.className = "variant-card-header";

  const headingGroup = document.createElement("div");

  const badge = document.createElement("span");
  badge.className = "variant-count pill pill-blue";
  badge.textContent = `Variant ${index}`;

  const title = document.createElement("h3");
  title.textContent = variant.title || `Optimized Variant ${index}`;

  headingGroup.appendChild(badge);
  headingGroup.appendChild(title);

  const copyButton = createCopyButton(variant.code || "");
  header.appendChild(headingGroup);
  header.appendChild(copyButton);

  const summary = document.createElement("p");
  summary.className = "variant-summary";
  summary.textContent = variant.summary || "Output-preserving optimized rewrite with dead code removed where possible.";

  const codeShell = document.createElement("div");
  codeShell.className = "variant-code-shell";

  const code = document.createElement("pre");
  code.className = "variant-code";
  code.textContent = variant.code || "";
  codeShell.appendChild(code);
  codeShell.appendChild(createScrollControls(code, createExpandButton({
    kicker: `Variant ${index}`,
    title: variant.title || `Optimized Variant ${index}`,
    summary: variant.summary || "Output-preserving optimized rewrite with dead code removed where possible.",
    code: variant.code || ""
  })));

  card.appendChild(header);
  card.appendChild(summary);
  card.appendChild(codeShell);
  return card;
}

function renderVariants(variants) {
  variantsGrid.innerHTML = "";
  for (const [index, variant] of variants.entries()) {
    variantsGrid.appendChild(createVariantCard(variant, index + 1));
  }
}

async function loadVariants() {
  activeRequest = readStoredRequest();

  if (!activeRequest?.code) {
    setEmptyState(true);
    setStatus("No source code was passed from the main dashboard.", true);
    setSourceCode("Open this page from the main dashboard after entering code.");
    variantSourceMeta.textContent = "Use the AI Optimization button on the main studio page.";
    return;
  }

  const languageLabel = getLanguageLabel(activeRequest.language);
  const requestedCount = getRequestedCount();

  setEmptyState(false);
  setSourceCode(activeRequest.code);
  variantSourceMeta.textContent = `${languageLabel} source loaded. Requesting up to ${requestedCount} output-preserving optimized rewrites with dead-code removal for all valid test cases.`;
  regenerateVariantsBtn.disabled = true;
  if (variantCountInput) {
    variantCountInput.disabled = true;
  }
  setStatus(`Generating up to ${requestedCount} output-preserving optimized ${languageLabel} variants with dead-code removal...`);

  try {
    const resp = await fetch("/ai/variants", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code: activeRequest.code,
        language: activeRequest.language,
        count: requestedCount
      })
    });

    const data = await resp.json();
    if (!resp.ok || !data.ok) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    renderVariants(data.variants || []);
    const variantLabel = data.variants.length === 1 ? "version" : "versions";
    const suffix = data.warning ? ` ${data.warning}` : "";
    setStatus(`Generated ${data.variants.length} output-preserving optimized ${languageLabel} ${variantLabel}.${suffix}`);
  } catch (err) {
    variantsGrid.innerHTML = "";
    setStatus(`Error: ${err.message}`, true);
  } finally {
    regenerateVariantsBtn.disabled = false;
    if (variantCountInput) {
      variantCountInput.disabled = false;
    }
  }
}

backToStudioBtn.addEventListener("click", () => {
  try {
    sessionStorage.setItem(RETURN_TO_STUDIO_KEY, "1");
  } catch (_err) {
    // Ignore session storage errors and still navigate back.
  }

  window.location.href = "/";
});

regenerateVariantsBtn.addEventListener("click", loadVariants);

sourceCodeOut.addEventListener("scroll", () => {
  syncLineNumberScroll(sourceCodeOut, sourceLineNumbers);
});

variantFocusCode.addEventListener("scroll", () => {
  syncLineNumberScroll(variantFocusCode, variantFocusLineNumbers);
});

variantFocusCopyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(focusedVariantCode);
    const previous = variantFocusCopyBtn.textContent;
    variantFocusCopyBtn.textContent = "Copied";
    window.setTimeout(() => {
      variantFocusCopyBtn.textContent = previous;
    }, 1200);
  } catch (_err) {
    variantFocusCopyBtn.textContent = "Copy Failed";
  }
});

variantFocusCloseBtn.addEventListener("click", closeVariantFocus);

variantFocusOverlay.addEventListener("click", (event) => {
  if (event.target === variantFocusOverlay) {
    closeVariantFocus();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !variantFocusOverlay.classList.contains("hidden")) {
    event.preventDefault();
    closeVariantFocus();
  }
});

ensureStaticScrollControls();
loadVariants();
