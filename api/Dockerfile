# ── builder: install deps into a clean prefix ──────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /build
COPY api/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── runtime: minimal image ──────────────────────────────────────────────────
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /install /usr/local
COPY api/app /app/app
COPY pipeline /app/pipeline
COPY models /app/models
COPY data /app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
