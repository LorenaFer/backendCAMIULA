# ── Stage 0: Dev (hot-reload, código montado como volumen) ────
FROM python:3.11-slim AS dev

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# El código se monta como volumen en docker-compose, no se copia aquí.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Stage 1: Builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Build deps for asyncpg/bcrypt wheels (kept out of runtime image)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Ensure startup script is executable (in case host fs lost the bit)
RUN chmod +x /app/start.sh

# Railway injects PORT env var
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
EXPOSE ${PORT}

# Run migrations + uvicorn via startup script
CMD ["/app/start.sh"]
