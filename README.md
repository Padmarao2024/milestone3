# Recommender Project

This repository now includes the milestone 3 pipeline refactor and evaluation stack for a Kafka-backed recommender system.

## Pipeline Structure

The code is organized around a shared `pipeline/` package with explicit module boundaries:

- `pipeline/config.py`: env-based config for Kafka, snapshots, paths, and evaluation thresholds
- `pipeline/quality.py`: pandera schema validation, drift checks, and backpressure buffering
- `pipeline/transform.py`: snapshot loading and interaction table construction
- `pipeline/train.py`: popularity, item-item, and ALS training + serialization
- `pipeline/serve.py`: model loading and recommendation serving logic
- `pipeline/eval.py`: offline eval, online KPI computation from Kafka logs, and benchmarking

Thin script entrypoints remain under `training/`, `ingestor/`, and `api/` so the operational flow is clear:

`ingest -> transform -> train -> serialize -> serve -> eval`

## Kafka Setup

Required topics:

- `TEAM.watch`
- `TEAM.rate`
- `TEAM.reco_requests`
- `TEAM.reco_responses`

Core env vars:

- `KAFKA_BOOTSTRAP_SERVERS`
- `TEAM`
- `KAFKA_SECURITY_PROTOCOL`
- `KAFKA_USERNAME` / `KAFKA_PASSWORD` or SSL client cert paths
- `SNAPSHOT_BASE_PATH`
- `SNAPSHOT_FORMAT`
- `SNAPSHOT_BATCH_SIZE`
- `SNAPSHOT_HIGH_WATERMARK`

Create and verify topics:

```bash
bash scripts/create_topics.sh
bash scripts/verify_kafka.sh
```

## Training and Evaluation

Run the full offline pipeline:

```bash
bash scripts/train_all.sh
```

This generates:

- `report/offline_metrics.csv`
- `report/offline_subpopulations.csv`
- `report/benchmark.csv`
- `report/drift_report.csv`

Compute online KPI from `TEAM.reco_responses`:

```bash
python training/online_eval.py
```

This generates:

- `report/online_kpi_summary.csv`
- `report/online_kpi_by_model.csv`

## Quality Gates

Quality gates implemented for milestone 3:

- Unit tests in `tests/`
- Pandera schema validation for watch, rate, and reco-response payloads
- Drift report on user/item distributions in `report/drift_report.csv`
- Backpressure handling in `ingestor/consumer.py` using high-watermark buffering and pause/resume logic

Run locally:

```bash
ruff check .
pytest --cov=pipeline --cov=ingestor --cov-report=term-missing --cov-fail-under=70
```

## API

Build and run locally:

```bash
docker buildx build --platform linux/amd64 -f api/Dockerfile -t recommender-api:latest .
docker run --rm -p 8000:8000 recommender-api:latest
```

Endpoints:

- `GET /health`
- `GET /recommend?user_id=u1&k=10`

## CI/CD

GitHub Actions workflows:

- `.github/workflows/probe.yml`: scheduled probe publisher
- `.github/workflows/ci-cd.yml`: lint, tests, coverage, image build/push, Azure Container Apps deploy on `main`

Secrets strategy for CI/CD:

- Docker Hub: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
- Azure Container Apps: `AZURE_CREDENTIALS`, `AZURE_CONTAINER_APP_NAME`, `AZURE_RESOURCE_GROUP`

## Submission Artifacts

Milestone evidence lives under `report/`.

- Milestone 2 evidence: `report/submission_evidence.md`
- Screenshots appendix: `report/submission_screenshots.pdf`
