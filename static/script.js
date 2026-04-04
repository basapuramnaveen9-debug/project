const languageSelect = document.getElementById("languageSelect");
const codeInputLabel = document.getElementById("codeInputLabel");
const editorShell = document.getElementById("codeEditorShell");
const codeEditorEl = document.getElementById("codeEditor");
const codeEditorPlaceholder = document.getElementById("codeEditorPlaceholder");
const codeInput = document.getElementById("codeInput");
const inputPanel = document.querySelector(".input-panel");
const optimizeBtn = document.getElementById("optimizeBtn");
const sampleBtn = document.getElementById("sampleBtn");
const fileMenuBtn = document.getElementById("fileMenuBtn");
const fileMenuPanel = document.getElementById("fileMenuPanel");
const openFileBtn = document.getElementById("openFileBtn");
const saveSourceBtn = document.getElementById("saveSourceBtn");
const saveOptimizedBtn = document.getElementById("saveOptimizedBtn");
const sourceFileInput = document.getElementById("sourceFileInput");
const currentFileNameEl = document.getElementById("currentFileName");
const toggleFocusModeBtn = document.getElementById("toggleFocusModeBtn");
const toggleOptimizedFocusBtn = document.getElementById("toggleOptimizedFocusBtn");
const toggleExecutionFocusBtn = document.getElementById("toggleExecutionFocusBtn");
const aiOptimizePageBtn = document.getElementById("aiOptimizePageBtn");
const aiSuggestionsActions = document.querySelector(".ai-suggestions-actions");
const stopBtn = document.getElementById("stopBtn");
const executionControls = document.getElementById("executionControls");
const executionHelp = document.getElementById("executionHelp");
const statusEl = document.getElementById("status");
const focusModeHint = document.getElementById("focusModeHint");
const optimizedResultBlock = document.getElementById("optimizedResultBlock");
const executionResultBlock = document.getElementById("executionResultBlock");
const optimizedPanel = document.getElementById("optimizedPanel");

const optimizedLineNumbers = document.getElementById("optimizedLineNumbers");
const optimizedCodeEditorEl = document.getElementById("optimizedCodeEditor");
const optimizedOut = document.getElementById("optimizedOut");
const aiOut = document.getElementById("aiOut");
const algoOut = document.getElementById("algoOut");
const complexityBeforeOut = document.getElementById("complexityBeforeOut");
const complexityAfterOut = document.getElementById("complexityAfterOut");
const complexityBeforeBar = document.getElementById("complexityBeforeBar");
const complexityAfterBar = document.getElementById("complexityAfterBar");
const spaceBeforeOut = document.getElementById("spaceBeforeOut");
const spaceAfterOut = document.getElementById("spaceAfterOut");
const spaceBeforeBar = document.getElementById("spaceBeforeBar");
const spaceAfterBar = document.getElementById("spaceAfterBar");
const loopsBeforeOut = document.getElementById("loopsBeforeOut");
const loopsAfterOut = document.getElementById("loopsAfterOut");
const loopsBeforeBar = document.getElementById("loopsBeforeBar");
const loopsAfterBar = document.getElementById("loopsAfterBar");
const runtimeBeforeOut = document.getElementById("runtimeBeforeOut");
const runtimeAfterOut = document.getElementById("runtimeAfterOut");
const runtimeBeforeBar = document.getElementById("runtimeBeforeBar");
const runtimeAfterBar = document.getElementById("runtimeAfterBar");
const linesBeforeOut = document.getElementById("linesBeforeOut");
const linesAfterOut = document.getElementById("linesAfterOut");
const executionOut = document.getElementById("executionOut");
const OPTIMIZED_PLACEHOLDER = optimizedOut ? optimizedOut.textContent : "";

const MONACO_VERSION = "0.55.1";
const MONACO_BASE_URL = `https://cdn.jsdelivr.net/npm/monaco-editor@${MONACO_VERSION}/min/vs`;
const PYTHON_INDENT = "    ";
const DESKTOP_EDITOR_MIN_HEIGHT = 520;
const MOBILE_EDITOR_MIN_HEIGHT = 360;
const DESKTOP_FOCUS_EDITOR_OFFSET = 320;
const MOBILE_FOCUS_EDITOR_OFFSET = 280;
const AI_OPTIMIZATION_STORAGE_KEY = "rtrp-ai-optimization-request";
const AI_OPTIMIZATION_RETURN_KEY = "rtrp-ai-optimization-return";
const SOURCE_FILE_ACCEPT = ".c,.cpp,.cc,.cxx,.java,.py,.js,.ts,.go,.rs,.cs,.php,.rb,.kt";
const PRIMARY_LANGUAGE_OPTIONS = ["c", "cpp", "java", "python"];
const MORE_LANGUAGE_OPTIONS = ["javascript", "typescript", "go", "rust", "csharp", "php", "ruby", "kotlin"];
const MORE_SENTINEL_LANGUAGE = "more";

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

const languageExtensions = {
  c: ".c",
  cpp: ".cpp",
  java: ".java",
  python: ".py",
  javascript: ".js",
  typescript: ".ts",
  go: ".go",
  rust: ".rs",
  csharp: ".cs",
  php: ".php",
  ruby: ".rb",
  kotlin: ".kt"
};

const languageDefaultFilenames = {
  c: "main",
  cpp: "main",
  java: "Main",
  python: "main",
  javascript: "main",
  typescript: "main",
  go: "main",
  rust: "main",
  csharp: "Program",
  php: "index",
  ruby: "main",
  kotlin: "Main"
};

const monacoLanguages = {
  c: "c",
  cpp: "cpp",
  java: "java",
  python: "python",
  javascript: "javascript",
  typescript: "typescript",
  go: "go",
  rust: "rust",
  csharp: "csharp",
  php: "php",
  ruby: "ruby",
  kotlin: "kotlin"
};

const monacoSuggestions = {
  c: [
    {
      label: "main",
      kind: "Snippet",
      detail: "C entry point",
      insertText: ["int main(void) {", "    ${1:// code}", "    return 0;", "}"].join("\n")
    },
    {
      label: "printf",
      kind: "Function",
      detail: "Print formatted text",
      insertText: 'printf("${1:value}\\\\n"${2});'
    },
    {
      label: "for",
      kind: "Snippet",
      detail: "for loop",
      insertText: ["for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {", "    $0", "}"].join("\n")
    },
    {
      label: "while",
      kind: "Snippet",
      detail: "while loop",
      insertText: ["while (${1:condition}) {", "    $0", "}"].join("\n")
    },
    {
      label: "if",
      kind: "Snippet",
      detail: "if statement",
      insertText: ["if (${1:condition}) {", "    $0", "}"].join("\n")
    }
  ],
  cpp: [
    {
      label: "main",
      kind: "Snippet",
      detail: "C++ entry point",
      insertText: ["int main() {", "    ${1:// code}", "    return 0;", "}"].join("\n")
    },
    {
      label: "cout",
      kind: "Function",
      detail: "Write to stdout",
      insertText: 'std::cout << ${1:value} << "\\\\n";'
    },
    {
      label: "vector",
      kind: "Snippet",
      detail: "std::vector declaration",
      insertText: "std::vector<${1:int}> ${2:values};"
    },
    {
      label: "for",
      kind: "Snippet",
      detail: "for loop",
      insertText: ["for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {", "    $0", "}"].join("\n")
    },
    {
      label: "if",
      kind: "Snippet",
      detail: "if / else statement",
      insertText: ["if (${1:condition}) {", "    ${2:// code}", "} else {", "    $0", "}"].join("\n")
    }
  ],
  java: [
    {
      label: "class",
      kind: "Snippet",
      detail: "Java class",
      insertText: ["public class ${1:Main} {", "    $0", "}"].join("\n")
    },
    {
      label: "main",
      kind: "Snippet",
      detail: "main method",
      insertText: [
        "public static void main(String[] args) {",
        "    ${1:System.out.println(\"Hello, world!\");}",
        "}"
      ].join("\n")
    },
    {
      label: "println",
      kind: "Function",
      detail: "Print a line",
      insertText: "System.out.println(${1:value});"
    },
    {
      label: "for",
      kind: "Snippet",
      detail: "for loop",
      insertText: ["for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {", "    $0", "}"].join("\n")
    },
    {
      label: "scanner",
      kind: "Snippet",
      detail: "Scanner input",
      insertText: [
        "Scanner ${1:scanner} = new Scanner(System.in);",
        "${2:int value = scanner.nextInt();}"
      ].join("\n")
    }
  ],
  python: [
    {
      label: "def",
      kind: "Snippet",
      detail: "Function definition",
      insertText: ["def ${1:function_name}(${2:args}):", "    $0"].join("\n")
    },
    {
      label: "ifmain",
      kind: "Snippet",
      detail: "Run as script",
      insertText: ['if __name__ == "__main__":', "    $0"].join("\n")
    },
    {
      label: "for",
      kind: "Snippet",
      detail: "for loop",
      insertText: ["for ${1:item} in ${2:items}:", "    $0"].join("\n")
    },
    {
      label: "print",
      kind: "Function",
      detail: "Print output",
      insertText: "print(${1:value})"
    },
    {
      label: "class",
      kind: "Snippet",
      detail: "Class definition",
      insertText: ["class ${1:MyClass}:", "    def __init__(self, ${2:value}):", "        self.${2:value} = ${2:value}", "", "    $0"].join("\n")
    }
  ],
  javascript: [
    {
      label: "function",
      kind: "Snippet",
      detail: "Function declaration",
      insertText: ["function ${1:name}(${2:args}) {", "  $0", "}"].join("\n")
    },
    {
      label: "forof",
      kind: "Snippet",
      detail: "for...of loop",
      insertText: ["for (const ${1:item} of ${2:items}) {", "  $0", "}"].join("\n")
    }
  ],
  typescript: [
    {
      label: "function",
      kind: "Snippet",
      detail: "Typed function declaration",
      insertText: ["function ${1:name}(${2:value}: ${3:number}): ${4:void} {", "  $0", "}"].join("\n")
    },
    {
      label: "interface",
      kind: "Snippet",
      detail: "Interface declaration",
      insertText: ["interface ${1:Name} {", "  ${2:key}: ${3:string};", "}"].join("\n")
    }
  ],
  go: [
    {
      label: "main",
      kind: "Snippet",
      detail: "Go entry point",
      insertText: ["func main() {", "\t$0", "}"].join("\n")
    }
  ],
  rust: [
    {
      label: "main",
      kind: "Snippet",
      detail: "Rust entry point",
      insertText: ["fn main() {", "    $0", "}"].join("\n")
    }
  ],
  csharp: [
    {
      label: "main",
      kind: "Snippet",
      detail: "C# entry point",
      insertText: ["static void Main(string[] args)", "{", "    $0", "}"].join("\n")
    }
  ],
  php: [
    {
      label: "foreach",
      kind: "Snippet",
      detail: "foreach loop",
      insertText: ["foreach (${1:$items} as ${2:$item}) {", "    $0", "}"].join("\n")
    }
  ],
  ruby: [
    {
      label: "each",
      kind: "Snippet",
      detail: "each loop",
      insertText: ["${1:items}.each do |${2:item}|", "  $0", "end"].join("\n")
    }
  ],
  kotlin: [
    {
      label: "main",
      kind: "Snippet",
      detail: "Kotlin entry point",
      insertText: ["fun main() {", "    $0", "}"].join("\n")
    }
  ]
};

let activeLanguage = languageLabels[languageSelect?.value] ? languageSelect.value : "c";
let languageMenuExpanded = MORE_LANGUAGE_OPTIONS.includes(activeLanguage);

let activeSessionId = null;
let executionCursor = 0;
let pollTimer = null;
let executionBuffer = "";
let pendingInput = "";
let sendingInput = false;
let monacoApi = null;
let monacoEditor = null;
let optimizedMonacoEditor = null;
let monacoLoaderPromise = null;
let monacoProvidersRegistered = false;
let optimizedPanelHeightObserver = null;
let activeResultPanel = "";
let currentSourceFileName = "";
let latestAiSuggestionRequestId = 0;

function isFileMenuOpen() {
  return Boolean(fileMenuPanel && !fileMenuPanel.classList.contains("hidden"));
}

function setFileMenuOpen(active) {
  if (!fileMenuBtn || !fileMenuPanel) {
    return;
  }

  fileMenuPanel.classList.toggle("hidden", !active);
  fileMenuBtn.classList.toggle("is-active", active);
  fileMenuBtn.setAttribute("aria-expanded", String(active));
}

function getLanguage() {
  return activeLanguage || "c";
}

function getLanguageLabel() {
  return languageLabels[getLanguage()] || "C";
}

function isPrimaryLanguage(language) {
  return PRIMARY_LANGUAGE_OPTIONS.includes(language);
}

function isMoreLanguage(language) {
  return MORE_LANGUAGE_OPTIONS.includes(language);
}

function appendLanguageOption(parent, value, label) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  parent.appendChild(option);
}

function renderLanguageSelect(selectedValue = activeLanguage) {
  if (!languageSelect) {
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const language of PRIMARY_LANGUAGE_OPTIONS) {
    appendLanguageOption(fragment, language, languageLabels[language]);
  }

  appendLanguageOption(fragment, MORE_SENTINEL_LANGUAGE, "More");

  if (languageMenuExpanded || isMoreLanguage(selectedValue)) {
    const moreGroup = document.createElement("optgroup");
    moreGroup.label = "More";
    for (const language of MORE_LANGUAGE_OPTIONS) {
      appendLanguageOption(moreGroup, language, languageLabels[language]);
    }
    fragment.appendChild(moreGroup);
  }

  languageSelect.replaceChildren(fragment);
  languageSelect.value = languageLabels[selectedValue] ? selectedValue : MORE_SENTINEL_LANGUAGE;
}

function setSelectedLanguage(language) {
  const nextLanguage = languageLabels[language] ? language : "c";
  activeLanguage = nextLanguage;
  languageMenuExpanded = isMoreLanguage(nextLanguage);
  renderLanguageSelect(nextLanguage);
}

function getMonacoLanguage() {
  return monacoLanguages[getLanguage()] || "plaintext";
}

function getLanguageExtension(language = getLanguage()) {
  return languageExtensions[language] || ".txt";
}

function isUsingMonaco() {
  return Boolean(monacoEditor);
}

function isUsingOptimizedMonaco() {
  return Boolean(optimizedMonacoEditor);
}

function prefersFallbackEditor() {
  if (typeof window.matchMedia !== "function") {
    return false;
  }

  return window.matchMedia("(pointer: coarse)").matches;
}

function isWritingModeActive() {
  return document.body.classList.contains("writing-focus");
}

function getCodeInputMinHeight() {
  const isMobile = typeof window.matchMedia === "function"
    && window.matchMedia("(max-width: 720px)").matches;
  const minHeight = isMobile ? MOBILE_EDITOR_MIN_HEIGHT : DESKTOP_EDITOR_MIN_HEIGHT;

  if (isWritingModeActive()) {
    const panelHeight = Math.round(inputPanel?.getBoundingClientRect().height || 0);
    if (panelHeight > 0) {
      return Math.max(panelHeight, minHeight);
    }

    const offset = isMobile ? MOBILE_FOCUS_EDITOR_OFFSET : DESKTOP_FOCUS_EDITOR_OFFSET;
    return Math.max(window.innerHeight - offset, minHeight);
  }

  return minHeight;
}

function resizeFallbackCodeInput() {
  if (!codeInput || isUsingMonaco()) {
    return;
  }

  const nextHeight = getCodeInputMinHeight();
  codeInput.style.height = `${nextHeight}px`;

  if (editorShell) {
    editorShell.style.height = `${nextHeight}px`;
  }
}

function syncMonacoEditorHeight() {
  if (!isUsingMonaco()) {
    return;
  }

  const nextHeight = getCodeInputMinHeight();
  const currentHeight = Math.round(codeEditorEl.getBoundingClientRect().height);

  if (currentHeight === nextHeight) {
    return;
  }

  codeEditorEl.style.height = `${nextHeight}px`;

  if (editorShell) {
    editorShell.style.height = `${nextHeight}px`;
  }

  monacoEditor.layout({ width: codeEditorEl.clientWidth, height: nextHeight });
}

function syncCodeInputHeight() {
  if (isUsingMonaco()) {
    syncMonacoEditorHeight();
    return;
  }

  resizeFallbackCodeInput();
}

function syncOptimizedPanelHeight() {
  if (!executionOut || !document.documentElement) {
    return;
  }

  const nextHeight = Math.round(executionOut.getBoundingClientRect().height || 0);
  if (nextHeight <= 0) {
    return;
  }

  document.documentElement.style.setProperty("--matched-output-panel-height", `${nextHeight}px`);
}

function setupOptimizedPanelHeightSync() {
  syncOptimizedPanelHeight();

  if (typeof ResizeObserver !== "function" || !executionOut) {
    return;
  }

  if (optimizedPanelHeightObserver) {
    optimizedPanelHeightObserver.disconnect();
  }

  optimizedPanelHeightObserver = new ResizeObserver(() => {
    syncOptimizedPanelHeight();
  });
  optimizedPanelHeightObserver.observe(executionOut);
}

function getCodeValue() {
  return isUsingMonaco() ? monacoEditor.getValue() : codeInput.value;
}

function setCodeValue(value) {
  const nextValue = value || "";
  codeInput.value = nextValue;

  if (isUsingMonaco() && monacoEditor.getValue() !== nextValue) {
    monacoEditor.setValue(nextValue);
  }

  syncCodeEditorPlaceholder();
  syncCodeInputHeight();
}

function resetExecutionState() {
  executionCursor = 0;
  executionBuffer = "";
  pendingInput = "";
  renderExecution();
}

function normalizeFileBaseName(name) {
  return String(name || "")
    .trim()
    .replace(/[<>:"/\\|?*\u0000-\u001F]/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^[-.]+|[-.]+$/g, "");
}

function getFileBaseName(name) {
  const trimmedName = String(name || "").trim();
  if (!trimmedName) {
    return "";
  }

  return trimmedName.replace(/\.[^.]+$/, "");
}

function getJavaClassName(code) {
  const text = String(code || "");
  const publicClassMatch = text.match(/\bpublic\s+class\s+([A-Za-z_$][\w$]*)\b/);
  if (publicClassMatch) {
    return publicClassMatch[1];
  }

  const classMatch = text.match(/\bclass\s+([A-Za-z_$][\w$]*)\b/);
  return classMatch ? classMatch[1] : "";
}

function getSuggestedFileBaseName(language = getLanguage(), content = "") {
  if (language === "java") {
    return getJavaClassName(content)
      || normalizeFileBaseName(getFileBaseName(currentSourceFileName))
      || languageDefaultFilenames.java;
  }

  return normalizeFileBaseName(getFileBaseName(currentSourceFileName))
    || languageDefaultFilenames[language]
    || "program";
}

function buildSuggestedFilename(kind, content, language = getLanguage()) {
  const baseName = getSuggestedFileBaseName(language, content);
  const suffix = kind === "optimized" && language !== "java" ? "-optimized" : "";
  return `${baseName}${suffix}${getLanguageExtension(language)}`;
}

function setCurrentSourceFileName(name) {
  currentSourceFileName = String(name || "").trim();
  updateCurrentFileName();
}

function updateCurrentFileName() {
  if (!currentFileNameEl) {
    return;
  }

  const fallbackName = `Unsaved ${getLanguageLabel()} file (${getLanguageExtension()})`;
  const nextName = currentSourceFileName || fallbackName;
  currentFileNameEl.textContent = nextName;
  currentFileNameEl.title = nextName;
}

function detectLanguageFromFilename(filename) {
  const lowerName = String(filename || "").trim().toLowerCase();
  if (!lowerName) {
    return null;
  }

  if (lowerName.endsWith(".cpp") || lowerName.endsWith(".cc") || lowerName.endsWith(".cxx")) {
    return "cpp";
  }

  if (lowerName.endsWith(".java")) {
    return "java";
  }

  if (lowerName.endsWith(".py")) {
    return "python";
  }

  if (lowerName.endsWith(".js")) {
    return "javascript";
  }

  if (lowerName.endsWith(".ts")) {
    return "typescript";
  }

  if (lowerName.endsWith(".go")) {
    return "go";
  }

  if (lowerName.endsWith(".rs")) {
    return "rust";
  }

  if (lowerName.endsWith(".cs")) {
    return "csharp";
  }

  if (lowerName.endsWith(".php")) {
    return "php";
  }

  if (lowerName.endsWith(".rb")) {
    return "ruby";
  }

  if (lowerName.endsWith(".kt")) {
    return "kotlin";
  }

  if (lowerName.endsWith(".c")) {
    return "c";
  }

  return null;
}

function getFilePickerTypes(language = getLanguage()) {
  return [{
    description: `${languageLabels[language] || "Source"} files`,
    accept: { "text/plain": [getLanguageExtension(language)] }
  }];
}

function triggerTextDownload(content, filename) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

async function saveTextToDevice(content, kind) {
  const trimmedContent = String(content || "");
  if (!trimmedContent.trim()) {
    statusEl.textContent = kind === "optimized" ? "Run analysis before saving optimized code." : "Enter code first.";
    if (kind === "source") {
      focusCodeInput();
    }
    return;
  }

  const language = getLanguage();
  const suggestedName = buildSuggestedFilename(kind, trimmedContent, language);

  try {
    if (typeof window.showSaveFilePicker === "function") {
      const handle = await window.showSaveFilePicker({
        suggestedName,
        types: getFilePickerTypes(language)
      });
      const writable = await handle.createWritable();
      await writable.write(trimmedContent);
      await writable.close();

      if (kind === "source") {
        setCurrentSourceFileName(handle.name || suggestedName);
      }

      statusEl.textContent = `${handle.name || suggestedName} saved to your PC.`;
      return;
    }

    triggerTextDownload(trimmedContent, suggestedName);
    if (kind === "source") {
      setCurrentSourceFileName(suggestedName);
    }
    statusEl.textContent = `${suggestedName} download started.`;
  } catch (err) {
    if (err?.name === "AbortError") {
      return;
    }

    statusEl.textContent = `Error: ${err.message}`;
  }
}

async function changeWorkspaceLanguage(language, options = {}) {
  const {
    clearCode = true,
    resetFileName = clearCode,
    focusEditor = true,
    statusMessage = `${languageLabels[language] || "Code"} selected.`
  } = options;

  const nextLanguage = languageLabels[language] ? language : "c";
  setSelectedLanguage(nextLanguage);

  await stopActiveSession(true);
  resetExecutionState();
  clearAnalysis();

  if (clearCode) {
    setCodeValue("");
  }

  if (resetFileName) {
    setCurrentSourceFileName("");
  } else {
    updateCurrentFileName();
  }

  updateLanguageUI();

  if (focusEditor) {
    focusCodeInput();
  }

  if (statusMessage) {
    statusEl.textContent = statusMessage;
  }
}

async function loadSourceFile(file) {
  if (!file) {
    return;
  }

  const fileText = await file.text();
  const detectedLanguage = detectLanguageFromFilename(file.name) || getLanguage();

  await changeWorkspaceLanguage(detectedLanguage, {
    clearCode: false,
    resetFileName: false,
    statusMessage: ""
  });

  setCodeValue(fileText);
  setCurrentSourceFileName(file.name);
  focusCodeInput();
  statusEl.textContent = `${file.name} loaded from your device.`;
}

async function openSourceFilePicker() {
  try {
    if (typeof window.showOpenFilePicker === "function") {
      const [handle] = await window.showOpenFilePicker({
        multiple: false,
        types: [
          {
            description: "Source code files",
            accept: {
              "text/plain": [".c", ".cpp", ".cc", ".cxx", ".java", ".py", ".js", ".ts", ".go", ".rs", ".cs", ".php", ".rb", ".kt"]
            }
          }
        ]
      });

      if (!handle) {
        return;
      }

      const file = await handle.getFile();
      await loadSourceFile(file);
      return;
    }

    if (sourceFileInput) {
      sourceFileInput.value = "";
      sourceFileInput.click();
    }
  } catch (err) {
    if (err?.name === "AbortError") {
      return;
    }

    statusEl.textContent = `Error: ${err.message}`;
  }
}

function getOptimizedContent() {
  const content = String(isUsingOptimizedMonaco()
    ? optimizedMonacoEditor.getValue()
    : optimizedOut?.textContent || "");
  return content === OPTIMIZED_PLACEHOLDER ? "" : content;
}

function focusCodeInput() {
  if (isUsingMonaco()) {
    monacoEditor.focus();
    return;
  }

  codeInput.focus();
}

function setCodePlaceholder(text) {
  codeInput.placeholder = text;

  if (codeEditorPlaceholder) {
    codeEditorPlaceholder.textContent = text;
  }

  syncCodeEditorPlaceholder();
}

function syncCodeEditorPlaceholder() {
  if (!codeEditorPlaceholder) {
    return;
  }

  const shouldHide = !isUsingMonaco() || getCodeValue().length > 0 || monacoEditor.hasTextFocus();
  codeEditorPlaceholder.classList.toggle("hidden", shouldHide);
}

function setAiOptimizationVisibility(visible) {
  if (!aiSuggestionsActions) {
    return;
  }

  aiSuggestionsActions.classList.toggle("hidden", !visible);
}

function setToggleButtonState(button, active, inactiveLabel, activeLabel) {
  if (!button) {
    return;
  }

  button.setAttribute("aria-pressed", String(active));
  button.classList.toggle("is-active", active);
  button.setAttribute("aria-label", active ? activeLabel : inactiveLabel);
  button.setAttribute("title", active ? activeLabel : inactiveLabel);
}

function isResultPanelFocusActive(panelName) {
  return panelName ? activeResultPanel === panelName : Boolean(activeResultPanel);
}

function setResultPanelFocus(panelName) {
  const nextPanel = panelName || "";
  activeResultPanel = nextPanel;

  document.body.classList.toggle("panel-focus-active", Boolean(nextPanel));

  if (nextPanel) {
    document.body.dataset.focusPanel = nextPanel;
  } else {
    delete document.body.dataset.focusPanel;
  }

  optimizedResultBlock?.classList.toggle("panel-focus-target", nextPanel === "optimized");
  executionResultBlock?.classList.toggle("panel-focus-target", nextPanel === "execution");

  setToggleButtonState(
    toggleOptimizedFocusBtn,
    nextPanel === "optimized",
    "Open full screen optimized code",
    "Close full screen optimized code"
  );
  setToggleButtonState(
    toggleExecutionFocusBtn,
    nextPanel === "execution",
    "Open full screen execution log",
    "Close full screen execution log"
  );

  if (nextPanel === "execution") {
    executionOut.focus();
    if (activeSessionId) {
      moveCaretToEnd();
    }
  } else if (nextPanel === "optimized" && isUsingOptimizedMonaco()) {
    optimizedMonacoEditor.focus();
  }
}

function toggleResultPanelFocus(panelName) {
  const nextPanel = activeResultPanel === panelName ? "" : panelName;
  if (nextPanel && isWritingModeActive()) {
    setWritingMode(false);
  }

  setResultPanelFocus(nextPanel);
}

function setWritingMode(active) {
  if (active && isResultPanelFocusActive()) {
    setResultPanelFocus("");
  }

  document.body.classList.toggle("writing-focus", active);

  setToggleButtonState(
    toggleFocusModeBtn,
    active,
    "Open full screen editor",
    "Close full screen editor"
  );

  if (focusModeHint) {
    focusModeHint.classList.toggle("hidden", !active);
  }

  syncCodeInputHeight();
  window.requestAnimationFrame(() => {
    syncCodeInputHeight();
    focusCodeInput();
  });
}

function toggleWritingMode(forceState) {
  const nextState = typeof forceState === "boolean" ? forceState : !isWritingModeActive();
  setWritingMode(nextState);
}

function openAiOptimizationPage() {
  const code = getCodeValue().trim();
  if (!code) {
    statusEl.textContent = "Enter code first.";
    focusCodeInput();
    return;
  }

  const requestPayload = {
    code,
    language: getLanguage(),
    fileName: currentSourceFileName,
    createdAt: Date.now()
  };

  try {
    sessionStorage.setItem(AI_OPTIMIZATION_STORAGE_KEY, JSON.stringify(requestPayload));
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
    return;
  }

  window.location.href = "/ai-optimization";
}

function restoreStudioStateFromAiOptimization() {
  try {
    const shouldRestore = sessionStorage.getItem(AI_OPTIMIZATION_RETURN_KEY) === "1";
    if (!shouldRestore) {
      return;
    }

    sessionStorage.removeItem(AI_OPTIMIZATION_RETURN_KEY);
    const rawRequest = sessionStorage.getItem(AI_OPTIMIZATION_STORAGE_KEY);
    const request = rawRequest ? JSON.parse(rawRequest) : null;
    if (!request?.code) {
      return;
    }

    const language = languageLabels[request.language] ? request.language : "c";
    setSelectedLanguage(language);
    updateLanguageUI();
    setCodeValue(request.code);
    setCurrentSourceFileName(request.fileName || "");
    clearAnalysis();
    resetExecutionState();
    statusEl.textContent = `${getLanguageLabel()} input code restored from AI Optimization.`;
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  }
}

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

function renderAiSuggestionsLoading() {
  aiOut.innerHTML = "";
  const li = document.createElement("li");
  li.className = "loading-list-item";

  const spinner = document.createElement("span");
  spinner.className = "loading-spinner";
  spinner.setAttribute("aria-hidden", "true");

  const text = document.createElement("span");
  text.textContent = "Loading AI suggestions...";

  li.appendChild(spinner);
  li.appendChild(text);
  aiOut.appendChild(li);
}

async function fetchAiSuggestions(code, language, requestId) {
  try {
    const resp = await fetch("/ai/suggestions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, language })
    });

    const data = await resp.json();
    if (requestId !== latestAiSuggestionRequestId) {
      return;
    }

    if (!resp.ok || !data.ok) {
      throw new Error(data.error || `HTTP ${resp.status}`);
    }

    renderList(aiOut, data.ai || []);
    setAiOptimizationVisibility(true);
  } catch (err) {
    if (requestId !== latestAiSuggestionRequestId) {
      return;
    }

    renderList(aiOut, [`AI suggestions are still unavailable: ${err.message}`]);
    setAiOptimizationVisibility(false);
  }
}

function formatMetricText(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

function formatNumber(value, decimals) {
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return "-";
  }
  return typeof decimals === "number" ? num.toFixed(decimals) : String(num);
}

function complexityScore(value) {
  if (value === null || value === undefined) {
    return null;
  }
  const text = String(value).toLowerCase();
  if (!text) {
    return null;
  }
  if (text.includes("o(1)")) {
    return 1;
  }
  if (text.includes("o(n log n)")) {
    return 4;
  }
  if (text.includes("o(n^3)")) {
    return 6;
  }
  if (text.includes("o(n^2)")) {
    return 5;
  }
  if (text.includes("o(n)")) {
    return 3;
  }
  return null;
}

function numericScore(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
}

function applySplitBar(beforeScore, afterScore, beforeBar, afterBar) {
  if (!beforeBar || !afterBar) {
    return;
  }

  const safeBefore = beforeScore ?? 0;
  const safeAfter = afterScore ?? 0;
  const maxScore = Math.max(safeBefore, safeAfter, 1);

  const beforePct = beforeScore === null ? 0 : Math.round((safeBefore / maxScore) * 100);
  const afterPct = afterScore === null ? 0 : Math.round((safeAfter / maxScore) * 100);

  beforeBar.style.width = `${beforePct}%`;
  afterBar.style.width = `${afterPct}%`;
}

function updateSplitMetric(options) {
  const {
    beforeValue,
    afterValue,
    beforeOut,
    afterOut,
    beforeBar,
    afterBar,
    type,
    decimals
  } = options;

  if (beforeOut) {
    beforeOut.textContent = type === "number"
      ? formatNumber(beforeValue, decimals)
      : formatMetricText(beforeValue);
  }
  if (afterOut) {
    afterOut.textContent = type === "number"
      ? formatNumber(afterValue, decimals)
      : formatMetricText(afterValue);
  }

  const beforeScore = type === "number" ? numericScore(beforeValue) : complexityScore(beforeValue);
  const afterScore = type === "number" ? numericScore(afterValue) : complexityScore(afterValue);

  applySplitBar(beforeScore, afterScore, beforeBar, afterBar);
}

function buildLineNumbers(text) {
  const lineCount = Math.max(String(text ?? "").split("\n").length, 1);
  return Array.from({ length: lineCount }, (_, index) => index + 1).join("\n");
}

function syncLineNumberScroll(sourceNode, gutterNode) {
  gutterNode.scrollTop = sourceNode.scrollTop;
}

function setCodeInputSelection(start, end = start) {
  codeInput.focus();
  codeInput.setSelectionRange(start, end);
}

function handlePythonTabIndentation(event) {
  if (isUsingMonaco() || getLanguage() !== "python" || event.key !== "Tab") {
    return false;
  }

  event.preventDefault();

  const { selectionStart, selectionEnd, value } = codeInput;

  if (!event.shiftKey) {
    codeInput.setRangeText(PYTHON_INDENT, selectionStart, selectionEnd, "end");
    return true;
  }

  const lineStart = value.lastIndexOf("\n", selectionStart - 1) + 1;
  const currentLine = value.slice(lineStart, selectionStart);
  const removableIndent = currentLine.match(/^[ ]{1,4}$/);

  if (!removableIndent) {
    return true;
  }

  const removeCount = removableIndent[0].length;
  codeInput.setRangeText("", selectionStart - removeCount, selectionStart, "end");
  setCodeInputSelection(selectionStart - removeCount, selectionEnd - removeCount);
  return true;
}

function handlePythonEnterIndentation(event) {
  if (isUsingMonaco() || getLanguage() !== "python" || event.key !== "Enter") {
    return false;
  }

  event.preventDefault();

  const { selectionStart, selectionEnd, value } = codeInput;
  const lineStart = value.lastIndexOf("\n", selectionStart - 1) + 1;
  const currentLineBeforeCursor = value.slice(lineStart, selectionStart);
  const currentIndent = (currentLineBeforeCursor.match(/^[ \t]*/) || [""])[0].replace(/\t/g, PYTHON_INDENT);
  const trimmedLine = currentLineBeforeCursor.trim();

  let nextIndent = currentIndent;

  if (currentLineBeforeCursor.match(/:\s*(#.*)?$/)) {
    nextIndent += PYTHON_INDENT;
  } else if (/^(return|break|continue|pass|raise)\b/.test(trimmedLine) && currentIndent.length >= PYTHON_INDENT.length) {
    nextIndent = currentIndent.slice(0, -PYTHON_INDENT.length);
  }

  codeInput.setRangeText(`\n${nextIndent}`, selectionStart, selectionEnd, "end");
  return true;
}

function setOptimizedOutput(text) {
  const content = text === null || text === undefined ? "" : String(text);
  optimizedOut.textContent = content;
  optimizedLineNumbers.textContent = buildLineNumbers(content);
  if (isUsingOptimizedMonaco()) {
    if (optimizedMonacoEditor.getValue() !== content) {
      optimizedMonacoEditor.setValue(content);
    }
  } else {
    syncLineNumberScroll(optimizedOut, optimizedLineNumbers);
  }
}

function clearAnalysis() {
  latestAiSuggestionRequestId += 1;
  setOptimizedOutput(OPTIMIZED_PLACEHOLDER);
  aiOut.innerHTML = "";
  algoOut.innerHTML = "";
  setAiOptimizationVisibility(false);
  updateSplitMetric({
    beforeValue: null,
    afterValue: null,
    beforeOut: complexityBeforeOut,
    afterOut: complexityAfterOut,
    beforeBar: complexityBeforeBar,
    afterBar: complexityAfterBar,
    type: "complexity"
  });
  updateSplitMetric({
    beforeValue: null,
    afterValue: null,
    beforeOut: spaceBeforeOut,
    afterOut: spaceAfterOut,
    beforeBar: spaceBeforeBar,
    afterBar: spaceAfterBar,
    type: "complexity"
  });
  updateSplitMetric({
    beforeValue: null,
    afterValue: null,
    beforeOut: loopsBeforeOut,
    afterOut: loopsAfterOut,
    beforeBar: loopsBeforeBar,
    afterBar: loopsAfterBar,
    type: "number",
    decimals: 0
  });
  updateSplitMetric({
    beforeValue: null,
    afterValue: null,
    beforeOut: runtimeBeforeOut,
    afterOut: runtimeAfterOut,
    beforeBar: runtimeBeforeBar,
    afterBar: runtimeAfterBar,
    type: "number",
    decimals: 6
  });
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
  syncOptimizedPanelHeight();
}

function updateCodeEditorLanguage() {
  if (!isUsingMonaco() || !monacoApi) {
    return;
  }

  const model = monacoEditor.getModel();
  if (!model) {
    return;
  }

  monacoApi.editor.setModelLanguage(model, getMonacoLanguage());
  model.updateOptions({ insertSpaces: true, tabSize: 4 });
}

function updateOptimizedEditorLanguage() {
  if (!isUsingOptimizedMonaco() || !monacoApi) {
    return;
  }

  const model = optimizedMonacoEditor.getModel();
  if (!model) {
    return;
  }

  monacoApi.editor.setModelLanguage(model, getMonacoLanguage());
  model.updateOptions({ insertSpaces: true, tabSize: 4 });
}

function updateLanguageUI() {
  const label = getLanguageLabel();
  setCodePlaceholder(`Paste ${label} code here...`);
  executionOut.placeholder = `Run analysis to see ${label} compiler or runtime output.`;
  executionHelp.textContent = `Type directly inside the console above and press Enter when your ${label} program asks for input.`;
  updateCurrentFileName();
  updateCodeEditorLanguage();
  updateOptimizedEditorLanguage();
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
    "unable to run the selected program",
    "runtime timed out",
    "compilation timed out",
    "compiler not found",
    "c++ compiler not found",
    "java compiler/runtime not found",
    "blocked the generated program",
    "program exited with code",
    "traceback (most recent call last)",
    "syntaxerror:",
    "exception in thread",
    "could not find or load main class",
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

      setAiOptimizationVisibility(true);
      statusEl.textContent = `${getLanguageLabel()} analysis finished.`;
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

function defineMonacoTheme(monaco) {
  monaco.editor.defineTheme("rtrp-studio", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "comment", foreground: "7D8FB3", fontStyle: "italic" },
      { token: "keyword", foreground: "57D7FF" },
      { token: "number", foreground: "FFC85E" },
      { token: "string", foreground: "55F0A7" },
      { token: "type", foreground: "9DDCFF" },
      { token: "delimiter.bracket", foreground: "DCE7FF" }
    ],
    colors: {
      "editor.background": "#0A1020",
      "editor.foreground": "#EFF7FF",
      "editorCursor.foreground": "#57D7FF",
      "editorLineNumber.foreground": "#60739B",
      "editorLineNumber.activeForeground": "#DCE7FF",
      "editor.lineHighlightBackground": "#0F1A33",
      "editor.selectionBackground": "#294F8A66",
      "editor.inactiveSelectionBackground": "#294F8A44",
      "editorIndentGuide.background1": "#263557",
      "editorIndentGuide.activeBackground1": "#57D7FF66",
      "editorWidget.background": "#10192F",
      "editorWidget.border": "#314D7A",
      "editorSuggestWidget.background": "#0D1427",
      "editorSuggestWidget.border": "#314D7A",
      "editorSuggestWidget.selectedBackground": "#173058",
      "editorHoverWidget.background": "#0D1427",
      "editorHoverWidget.border": "#314D7A",
      "scrollbarSlider.background": "#7B8FB333",
      "scrollbarSlider.hoverBackground": "#7B8FB355",
      "scrollbarSlider.activeBackground": "#9DBEFF88"
    }
  });
}

function toCompletionSuggestion(monaco, range, suggestion, index) {
  const kindName = suggestion.kind || "Text";
  const kind = monaco.languages.CompletionItemKind[kindName] || monaco.languages.CompletionItemKind.Text;

  return {
    label: suggestion.label,
    kind,
    detail: suggestion.detail,
    documentation: suggestion.documentation || suggestion.detail,
    insertText: suggestion.insertText,
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    range,
    sortText: `0${index}`
  };
}

function registerMonacoCompletionProviders(monaco) {
  if (monacoProvidersRegistered) {
    return;
  }

  for (const [language, suggestions] of Object.entries(monacoSuggestions)) {
    monaco.languages.registerCompletionItemProvider(language, {
      provideCompletionItems(model, position) {
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        };

        return {
          suggestions: suggestions.map((suggestion, index) => toCompletionSuggestion(monaco, range, suggestion, index))
        };
      }
    });
  }

  monacoProvidersRegistered = true;
}

function createMonacoWorkerUrl(workerPath) {
  const workerSource = [
    `self.MonacoEnvironment = { baseUrl: "${MONACO_BASE_URL}/" };`,
    `importScripts("${MONACO_BASE_URL}/${workerPath}.js");`
  ].join("\n");

  return `data:text/javascript;charset=utf-8,${encodeURIComponent(workerSource)}`;
}

function createMonacoModel(monaco, value, options = {}) {
  const { language = getMonacoLanguage(), name = "main" } = options;
  const uri = monaco.Uri.parse(`inmemory://model/${name}.${getLanguage()}`);
  const model = monaco.editor.createModel(value, language, uri);
  model.updateOptions({ insertSpaces: true, tabSize: 4 });
  return model;
}

function configureMonacoEditor(monaco) {
  defineMonacoTheme(monaco);
  registerMonacoCompletionProviders(monaco);

  const model = createMonacoModel(monaco, codeInput.value || "", {
    language: getMonacoLanguage(),
    name: "input"
  });
  const codeFont = getComputedStyle(document.documentElement).getPropertyValue("--code-font").trim();

  editorShell.classList.add("monaco-ready");
  monacoEditor = monaco.editor.create(codeEditorEl, {
    model,
    theme: "rtrp-studio",
    ariaLabel: "Input code editor",
    automaticLayout: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    smoothScrolling: true,
    roundedSelection: false,
    cursorBlinking: "smooth",
    renderLineHighlight: "all",
    fontFamily: codeFont || "Consolas, monospace",
    fontSize: 15,
    lineHeight: 26,
    padding: { top: 18, bottom: 18 },
    quickSuggestions: { other: true, comments: false, strings: true },
    suggestOnTriggerCharacters: true,
    snippetSuggestions: "top",
    bracketPairColorization: { enabled: true },
    wordWrap: "off",
    scrollbar: {
      vertical: "auto",
      horizontal: "auto",
      handleMouseWheel: true,
      alwaysConsumeMouseWheel: false,
      verticalScrollbarSize: 10,
      horizontalScrollbarSize: 10,
      useShadows: false
    },
    fixedOverflowWidgets: true
  });

  monacoEditor.onDidChangeModelContent(() => {
    codeInput.value = monacoEditor.getValue();
    syncCodeEditorPlaceholder();
    syncMonacoEditorHeight();
  });
  monacoEditor.onDidContentSizeChange(syncMonacoEditorHeight);
  monacoEditor.onDidFocusEditorText(syncCodeEditorPlaceholder);
  monacoEditor.onDidBlurEditorText(syncCodeEditorPlaceholder);
  monacoEditor.addAction({
    id: "run-analysis",
    label: "Run Analysis",
    keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
    run: () => {
      optimizeBtn.click();
    }
  });

  syncMonacoEditorHeight();
  syncCodeEditorPlaceholder();
}

function configureOptimizedMonacoEditor(monaco) {
  if (!optimizedCodeEditorEl) {
    return;
  }

  const model = createMonacoModel(monaco, optimizedOut?.textContent || "", {
    language: getMonacoLanguage(),
    name: "optimized"
  });
  const codeFont = getComputedStyle(document.documentElement).getPropertyValue("--code-font").trim();

  optimizedMonacoEditor = monaco.editor.create(optimizedCodeEditorEl, {
    model,
    theme: "rtrp-studio",
    ariaLabel: "Optimized code viewer",
    automaticLayout: true,
    readOnly: true,
    domReadOnly: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    smoothScrolling: true,
    roundedSelection: false,
    renderLineHighlight: "none",
    fontFamily: codeFont || "Consolas, monospace",
    fontSize: 15,
    lineHeight: 26,
    padding: { top: 14, bottom: 14 },
    wordWrap: "off",
    lineNumbers: "off",
    glyphMargin: false,
    folding: false,
    overviewRulerLanes: 0,
    scrollbar: {
      vertical: "auto",
      horizontal: "auto",
      handleMouseWheel: true,
      alwaysConsumeMouseWheel: false,
      verticalScrollbarSize: 10,
      horizontalScrollbarSize: 10,
      useShadows: false
    },
    fixedOverflowWidgets: true
  });

  optimizedPanel?.classList.add("monaco-ready");
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[data-loader-src="${src}"]`);
    if (existing) {
      if (existing.dataset.loaded === "true") {
        resolve();
        return;
      }

      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)), { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.dataset.loaderSrc = src;
    script.addEventListener("load", () => {
      script.dataset.loaded = "true";
      resolve();
    }, { once: true });
    script.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)), { once: true });
    document.head.appendChild(script);
  });
}

function loadMonaco() {
  if (window.monaco?.editor) {
    return Promise.resolve(window.monaco);
  }

  if (monacoLoaderPromise) {
    return monacoLoaderPromise;
  }

  monacoLoaderPromise = new Promise((resolve, reject) => {
    const initializeLoader = () => {
      if (!window.require || typeof window.require.config !== "function") {
        reject(new Error("Monaco loader is unavailable."));
        return;
      }

      window.MonacoEnvironment = {
        getWorkerUrl(_moduleId, label) {
          if (label === "json") {
            return createMonacoWorkerUrl("language/json/json.worker");
          }

          if (["css", "scss", "less"].includes(label)) {
            return createMonacoWorkerUrl("language/css/css.worker");
          }

          if (["html", "handlebars", "razor"].includes(label)) {
            return createMonacoWorkerUrl("language/html/html.worker");
          }

          if (["javascript", "typescript"].includes(label)) {
            return createMonacoWorkerUrl("language/typescript/ts.worker");
          }

          return createMonacoWorkerUrl("editor/editor.worker");
        }
      };

      window.require.config({
        paths: {
          vs: MONACO_BASE_URL
        }
      });

      window.require(["vs/editor/editor.main"], () => resolve(window.monaco), (error) => {
        reject(error instanceof Error ? error : new Error("Failed to initialize Monaco Editor."));
      });
    };

    if (window.require && typeof window.require.config === "function") {
      initializeLoader();
      return;
    }

    loadScript(`${MONACO_BASE_URL}/loader.js`).then(initializeLoader).catch(reject);
  });

  return monacoLoaderPromise;
}

async function initializeCodeEditor() {
  if (!editorShell || !codeEditorEl || prefersFallbackEditor()) {
    syncCodeEditorPlaceholder();
    resizeFallbackCodeInput();
    return false;
  }

  try {
    monacoApi = await loadMonaco();
    configureMonacoEditor(monacoApi);
    configureOptimizedMonacoEditor(monacoApi);
    return true;
  } catch (err) {
    console.error(err);
    if (!statusEl.textContent.trim()) {
      statusEl.textContent = "Monaco Editor could not load. Using the basic editor.";
    }
    syncCodeEditorPlaceholder();
    return false;
  }
}

if (aiOptimizePageBtn) {
  aiOptimizePageBtn.addEventListener("click", openAiOptimizationPage);
}

if (toggleFocusModeBtn) {
  toggleFocusModeBtn.addEventListener("click", () => {
    toggleWritingMode();
  });
}

if (toggleOptimizedFocusBtn) {
  toggleOptimizedFocusBtn.addEventListener("click", () => {
    toggleResultPanelFocus("optimized");
  });
}

if (toggleExecutionFocusBtn) {
  toggleExecutionFocusBtn.addEventListener("click", () => {
    toggleResultPanelFocus("execution");
  });
}

if (fileMenuBtn) {
  fileMenuBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    setFileMenuOpen(!isFileMenuOpen());
  });
}

if (fileMenuPanel) {
  fileMenuPanel.addEventListener("click", (event) => {
    event.stopPropagation();
  });
}

if (openFileBtn) {
  openFileBtn.addEventListener("click", async () => {
    setFileMenuOpen(false);
    await openSourceFilePicker();
  });
}

if (saveSourceBtn) {
  saveSourceBtn.addEventListener("click", async () => {
    setFileMenuOpen(false);
    await saveTextToDevice(getCodeValue(), "source");
  });
}

if (saveOptimizedBtn) {
  saveOptimizedBtn.addEventListener("click", async () => {
    setFileMenuOpen(false);
    await saveTextToDevice(getOptimizedContent(), "optimized");
  });
}

if (sourceFileInput) {
  sourceFileInput.setAttribute("accept", SOURCE_FILE_ACCEPT);
  sourceFileInput.addEventListener("change", async (event) => {
    const [file] = Array.from(event.target.files || []);
    if (!file) {
      return;
    }

    try {
      await loadSourceFile(file);
    } catch (err) {
      statusEl.textContent = `Error: ${err.message}`;
    } finally {
      sourceFileInput.value = "";
    }
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && isFileMenuOpen()) {
    event.preventDefault();
    setFileMenuOpen(false);
    return;
  }

  if (event.key === "Escape" && isResultPanelFocusActive()) {
    event.preventDefault();
    setResultPanelFocus("");
    return;
  }

  if (event.key === "Escape" && isWritingModeActive()) {
    event.preventDefault();
    toggleWritingMode(false);
  }
});

document.addEventListener("click", () => {
  if (isFileMenuOpen()) {
    setFileMenuOpen(false);
  }
});

sampleBtn.addEventListener("click", async () => {
  const language = getLanguage();
  sampleBtn.disabled = true;
  statusEl.textContent = `Generating ${getLanguageLabel()} sample...`;

  try {
    await stopActiveSession(true);
    resetExecutionState();
    clearAnalysis();
    setCurrentSourceFileName("");

    const resp = await fetch(`/sample?language=${encodeURIComponent(language)}`);
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }

    const data = await resp.json();
    setCodeValue(data.code || "");
    focusCodeInput();
    statusEl.textContent = `${getLanguageLabel()} sample loaded.`;
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  } finally {
    sampleBtn.disabled = false;
  }
});

codeInput.addEventListener("input", syncCodeEditorPlaceholder);
codeInput.addEventListener("input", resizeFallbackCodeInput);
codeInput.addEventListener("focus", syncCodeEditorPlaceholder);
codeInput.addEventListener("blur", syncCodeEditorPlaceholder);
codeInput.addEventListener("keydown", (event) => {
  if (handlePythonTabIndentation(event)) {
    return;
  }

  handlePythonEnterIndentation(event);
});

optimizedOut.addEventListener("scroll", () => {
  if (isUsingOptimizedMonaco()) {
    return;
  }

  syncLineNumberScroll(optimizedOut, optimizedLineNumbers);
});

languageSelect.addEventListener("change", async () => {
  const selectedLanguage = languageSelect.value;

  if (selectedLanguage === MORE_SENTINEL_LANGUAGE) {
    languageMenuExpanded = true;
    renderLanguageSelect(MORE_SENTINEL_LANGUAGE);
    if (typeof languageSelect.showPicker === "function") {
      setTimeout(() => {
        languageSelect.focus();
        try {
          languageSelect.showPicker();
        } catch (_error) {
          // Ignore browsers that block programmatic picker opening.
        }
      }, 0);
    }
    return;
  }

  activeLanguage = languageLabels[selectedLanguage] ? selectedLanguage : "c";
  languageMenuExpanded = isMoreLanguage(activeLanguage);
  renderLanguageSelect(activeLanguage);
  await changeWorkspaceLanguage(activeLanguage);
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
  const code = getCodeValue().trim();
  const language = getLanguage();
  if (!code) {
    statusEl.textContent = "Enter code first.";
    focusCodeInput();
    return;
  }

  if (isWritingModeActive()) {
    toggleWritingMode(false);
  }

  optimizeBtn.disabled = true;
  sampleBtn.disabled = true;
  statusEl.textContent = `Running ${getLanguageLabel()} analysis...`;
  setAiOptimizationVisibility(false);
  latestAiSuggestionRequestId += 1;
  const suggestionRequestId = latestAiSuggestionRequestId;
  renderAiSuggestionsLoading();

  await stopActiveSession(true);
  resetExecutionState();
  fetchAiSuggestions(code, language, suggestionRequestId);

  try {
    const analysisResp = await fetch("/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, language })
    });

    if (!analysisResp.ok) {
      throw new Error(`HTTP ${analysisResp.status}`);
    }

    const data = await analysisResp.json();
    setOptimizedOutput(data.optimized || "");
    renderList(algoOut, data.algorithm || []);
    updateSplitMetric({
      beforeValue: data.complexity,
      afterValue: data.complexity_after,
      beforeOut: complexityBeforeOut,
      afterOut: complexityAfterOut,
      beforeBar: complexityBeforeBar,
      afterBar: complexityAfterBar,
      type: "complexity"
    });
    updateSplitMetric({
      beforeValue: data.space_complexity,
      afterValue: data.space_complexity_after,
      beforeOut: spaceBeforeOut,
      afterOut: spaceAfterOut,
      beforeBar: spaceBeforeBar,
      afterBar: spaceAfterBar,
      type: "complexity"
    });
    updateSplitMetric({
      beforeValue: data.loops,
      afterValue: data.loops_after,
      beforeOut: loopsBeforeOut,
      afterOut: loopsAfterOut,
      beforeBar: loopsBeforeBar,
      afterBar: loopsAfterBar,
      type: "number",
      decimals: 0
    });
    updateSplitMetric({
      beforeValue: data.runtime,
      afterValue: data.runtime_after,
      beforeOut: runtimeBeforeOut,
      afterOut: runtimeAfterOut,
      beforeBar: runtimeBeforeBar,
      afterBar: runtimeAfterBar,
      type: "number",
      decimals: 6
    });
    linesBeforeOut.textContent = data.lines_before ?? "-";
    linesAfterOut.textContent = data.lines_after ?? "-";

    const executeResp = await fetch("/execute/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, language })
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
    statusEl.textContent = `${getLanguageLabel()} program started. Type in the same console and press Enter if input is needed.`;
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

if (codeInputLabel) {
  codeInputLabel.addEventListener("click", (event) => {
    if (!isUsingMonaco()) {
      return;
    }

    event.preventDefault();
    focusCodeInput();
  });
}

renderLanguageSelect(activeLanguage);
updateLanguageUI();
setOptimizedOutput(optimizedOut.textContent);
renderExecution();
setAiOptimizationVisibility(false);
setResultPanelFocus("");
setWritingMode(false);
setFileMenuOpen(false);
syncCodeEditorPlaceholder();
resizeFallbackCodeInput();
restoreStudioStateFromAiOptimization();
setupOptimizedPanelHeightSync();
window.addEventListener("resize", () => {
  syncCodeInputHeight();
  syncOptimizedPanelHeight();
});
initializeCodeEditor();











