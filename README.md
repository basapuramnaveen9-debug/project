# RTRP Deployment

This project is now prepared for container-based deployment.

## What was added

- `Dockerfile` for production builds
- `gunicorn` for serving Flask in production
- `/healthz` endpoint for health checks
- `ENABLE_CODE_EXECUTION` toggle so deployed environments do not run submitted C code by default

## Important safety note

This app compiles and runs user-submitted C programs. That is a high-risk feature on a public server.

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

## Enable code execution

If you want the deployed app to compile and run C code inside the container:

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
