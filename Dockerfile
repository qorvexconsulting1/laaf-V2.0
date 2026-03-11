# ── LAAF Production Image ──────────────────────────────────────────────────────
# Multi-stage build: builder compiles deps, runtime image is lean (~200MB)
# arXiv:2507.10457 — Atta et al., Qorvex Research, 2026

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir hatchling

# Copy dependency files first — Docker layer cache only rebuilds on changes
COPY pyproject.toml README.md ./
COPY laaf/ ./laaf/
COPY configs/ ./configs/

# Build wheel into /wheels
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="LAAF"
LABEL org.opencontainers.image.description="Logic-layer Automated Attack Framework — Enterprise LPCI Red-Teaming for Agentic LLM Systems"
LABEL org.opencontainers.image.authors="Hammad Atta <hatta@qorvexconsulting.com>"
LABEL org.opencontainers.image.source="https://github.com/qorvexconsulting1/laaf"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.version="0.1.0"

WORKDIR /app

# Install pre-built wheels from builder — no compiler needed in runtime image
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --find-links /wheels laaf && \
    rm -rf /wheels

# Copy stage YAML configs
COPY configs/ ./configs/

# Create output and log directories
RUN mkdir -p /app/results /app/logs

# Non-root user — principle of least privilege
RUN useradd -m -u 1000 -s /bin/sh laaf && \
    chown -R laaf:laaf /app

USER laaf

# ── Environment defaults (override via .env or -e flags) ──────────────────────
ENV LAAF_API_HOST=0.0.0.0 \
    LAAF_API_PORT=8080 \
    LAAF_LOG_LEVEL=INFO \
    LAAF_OUTPUT_DIR=/app/results \
    LAAF_RATE_LIMIT_DELAY=2.0 \
    LAAF_MAX_ATTEMPTS_PER_STAGE=500 \
    OPENROUTER_API_KEY="" \
    OPENAI_API_KEY="" \
    ANTHROPIC_API_KEY="" \
    GOOGLE_API_KEY="" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Persist results and logs outside the container
VOLUME ["/app/results", "/app/logs"]

EXPOSE 8080

# Health check — polls the /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["laaf", "serve", "--host", "0.0.0.0", "--port", "8080"]
