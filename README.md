# Code Optimization Studio

Code Optimization Studio is a Flask-based code optimization workspace that analyzes source code, suggests improvements, generates AI-optimized variants, and runs programs in a browser-based interface.

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
OPENAI_API_KEY=your_provider_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=your-model-id
OPENAI_TIMEOUT_SECONDS=15
OPENAI_SUGGESTIONS_TIMEOUT_SECONDS=3.5
OPENAI_VARIANTS_TIMEOUT_SECONDS=12
OPENAI_MAX_SUGGESTIONS=6
AI_SUGGESTION_CACHE_TTL_SECONDS=900
FLASK_THREADED=true
```

Keep `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` aligned with the provider you actually use. If local development works because of `.env`, copy the same values into your deployed service's environment-variable or secret settings too.

The app also accepts these deployment aliases for the API key:

- `NVIDIA_API_KEY`
- `NIM_API_KEY`
- `AI_API_KEY`

If only `OPENAI_API_KEY` is present, the app defaults to `https://api.openai.com/v1` and `gpt-4o-mini`.
If only `NVIDIA_API_KEY` or `NIM_API_KEY` is present, the app defaults to `https://integrate.api.nvidia.com/v1` and `openai/gpt-oss-20b`.

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

The app can use locally installed tools when available. Some runtimes and toolchains can also be prepared automatically inside `.runtime_cache`.

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
docker build -t code-optimization-studio .
```

Run:

```bash
docker run --rm -p 8000:8000 -e PORT=8000 code-optimization-studio
```

With code execution enabled:

```bash
docker run --rm -p 8000:8000 -e PORT=8000 -e ENABLE_CODE_EXECUTION=true code-optimization-studio
```

With AI features configured:

```bash
docker run --rm -p 8000:8000 \
  -e PORT=8000 \
  -e OPENAI_API_KEY=your_provider_api_key_here \
  -e OPENAI_BASE_URL=https://api.openai.com/v1 \
  -e OPENAI_MODEL=your-model-id \
  code-optimization-studio
```

## Deployment Notes

Your local `.env` is ignored by Git and will usually not exist in a Git-based deployment. If the AI Optimization Lab shows a warning about `OPENAI_API_KEY` after deployment, the service is running but the remote environment is missing the AI provider settings.

At minimum, set these variables in your host dashboard or secret manager and redeploy:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

You can also use `NVIDIA_API_KEY`, `NIM_API_KEY`, or `AI_API_KEY` for the API key if that matches your provider setup better.

You can verify the deployment state at `/healthz`, which reports `ai_configured` plus the resolved key source, base URL, and model.

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
