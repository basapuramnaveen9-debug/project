# RTRP Deployment

This project is now prepared for container-based deployment.

## What was added

- `Dockerfile` for production builds
- `gunicorn` for serving Flask in production
- `/healthz` endpoint for health checks
- `ENABLE_CODE_EXECUTION` toggle so deployed environments do not run submitted C, C++, Java, or Python code by default

## Important safety note

This app compiles and runs user-submitted C, C++, Java, and Python programs. That is a high-risk feature on a public server.

- By default, deployed containers start with `ENABLE_CODE_EXECUTION=false`.
- Only enable execution if you trust the users and the host environment.
- For public internet exposure, use stronger sandboxing or isolate execution into a separate restricted service.

## Local Docker run

Build the image:

```bash
docker build -t rtrp .
```

Run it:

```bash
docker run --rm -p 8000:8000 -e PORT=8000 rtrp
```

Open:

```text
http://localhost:8000
```

## Configure the OpenAI API key

The AI suggestions feature reads `OPENAI_API_KEY`.

For local development, create a `.env` file in the repo root:

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_SUGGESTIONS_TIMEOUT_SECONDS=3.5
OPENAI_VARIANTS_TIMEOUT_SECONDS=12
```

The app now loads `.env` automatically on startup, and `.gitignore` excludes that file so your real key stays local.

The AI suggestions panel now falls back to local heuristics immediately and only waits a short time for remote AI enrichment. You can tune that short wait with `OPENAI_SUGGESTIONS_TIMEOUT_SECONDS`.

The AI variant generator also has a hard wall-clock cap. If the remote model is slow or unavailable, the app now returns locally optimized variants instead of leaving the page waiting. You can tune that cap with `OPENAI_VARIANTS_TIMEOUT_SECONDS`.

On Windows PowerShell, you can also set it for the current shell session:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
python app.py
```

## Enable code execution

If you want the deployed app to compile and run code inside the container:

```bash
docker run --rm -p 8000:8000 -e PORT=8000 -e ENABLE_CODE_EXECUTION=true rtrp
```

## Deploy to a host

Use any deployment platform that accepts a `Dockerfile`.

- Build from the repo root
- Expose port `8000` or set the platform `PORT` env var
- Keep a single app worker unless you move execution sessions out of process memory

## Health check

Use:

```text
/healthz
```

