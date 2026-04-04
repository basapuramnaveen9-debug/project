# RTRP

RTRP is a Flask-based code optimization studio that analyzes source code, suggests improvements, generates AI-optimized variants, and runs programs in a browser-based workspace.

## Highlights

- Browser UI for writing, optimizing, and running code
- AI suggestions plus a dedicated AI Optimization Lab
- Before/after metrics for complexity, space, loops, runtime, and line count
- Interactive execution console for programs that need stdin
- Multi-language execution support for:
  - C
  - C++
  - Java
  - Python
  - JavaScript
  - TypeScript
  - Go
  - Rust
  - C#
  - PHP
  - Ruby
  - Kotlin
- Automatic local runtime/toolchain bootstrap for selected languages through `.runtime_cache`

## Stack

- Backend: Flask
- Frontend: HTML, CSS, vanilla JavaScript
- AI integration: OpenAI-compatible API configuration via environment variables
- Runtime helpers: local toolchain detection plus cached runtime bootstrap

## Quick Start

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and set your values.

Example:

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=15
OPENAI_SUGGESTIONS_TIMEOUT_SECONDS=3.5
OPENAI_VARIANTS_TIMEOUT_SECONDS=12
OPENAI_MAX_SUGGESTIONS=6
AI_SUGGESTION_CACHE_TTL_SECONDS=900
FLASK_THREADED=true
```

### 4. Run the app

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Code Execution

Execution is controlled by `ENABLE_CODE_EXECUTION`.

- Local development defaults to enabled when Flask debug mode is on
- Deployed environments should keep it disabled unless execution is sandboxed

Example:

```powershell
$env:ENABLE_CODE_EXECUTION="true"
python app.py
```

## Runtime Notes

RTRP can use locally installed tools when available. Some runtimes/toolchains can also be prepared automatically inside `.runtime_cache`.

- JavaScript / TypeScript:
  - Uses `node`, `tsx`, `ts-node`, `deno`, or `bun` when available
  - Falls back to bundled Deno support when needed
- Go:
  - Uses system Go when available
  - Falls back to cached Go runtime support
- Kotlin:
  - Uses local `kotlinc` when available
  - Falls back to cached Kotlin compiler support
- Rust, .NET, PHP, Ruby, Node:
  - Resolver also checks common Windows install paths so recently installed tools work without relying only on the inherited `PATH`

## Docker

Build:

```bash
docker build -t rtrp .
```

Run:

```bash
docker run --rm -p 8000:8000 -e PORT=8000 rtrp
```

With code execution enabled:

```bash
docker run --rm -p 8000:8000 -e PORT=8000 -e ENABLE_CODE_EXECUTION=true rtrp
```

## Safety

This project can compile and run user-submitted code. That is a high-risk feature on untrusted infrastructure.

- Do not expose execution broadly without sandboxing
- Prefer isolated execution environments for public deployments
- Keep `ENABLE_CODE_EXECUTION=false` in environments you do not fully control

## Health Check

Use:

```text
/healthz
```

## Project Structure

```text
app.py                  Flask entrypoint
ai/                     AI suggestions and variant generation
analytics/              Benchmark and runtime estimation helpers
core/                   Execution, language, and compiler pipeline logic
optimizer/              Static optimization and analysis helpers
static/                 Frontend JavaScript, CSS, and assets
templates/              Flask HTML templates
```

## Release Notes

See [CHANGELOG.md](CHANGELOG.md) for versioned release notes.
