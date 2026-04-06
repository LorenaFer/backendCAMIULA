# ── Stage 1: Builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Railway injects PORT env var
ENV PORT=8000
EXPOSE ${PORT}

# Run with uvicorn — Railway expects the process to bind to $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2 --log-level info
