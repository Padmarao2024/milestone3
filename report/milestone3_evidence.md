# Milestone 3 Evidence Pack

## 1. Pipeline structure & config separation

Refactor outcome: the repo now uses a shared module layout with env-based config.

- `pipeline/config.py`: Kafka, snapshot, path, and eval thresholds from env.
- `pipeline/quality.py`: pandera schemas, drift checks, backpressure buffer.
- `pipeline/transform.py`: snapshot loading and interaction-table creation.
- `pipeline/train.py`: train + serialize Popularity, Item-Item, ALS.
- `pipeline/serve.py`: model loading and serving logic used by FastAPI.
- `pipeline/eval.py`: offline eval, online KPI, benchmark, drift report.

Operational entrypoints kept thin:

- `ingestor/consumer.py`
- `training/prepare_data.py`
- `training/evaluate.py`
- `training/online_eval.py`
- `training/drift_report.py`
- `api/app/recommender.py`

Backpressure handling is implemented in `ingestor/consumer.py` with `BackpressureBuffer`: when buffered events hit the high-water mark, consumer assignments are paused, batches are flushed, and then resumed.

## 2. Offline evaluation spec & results

Spec:

- Split: per-user chronological leave-last holdout (`chronological_leave_last`).
- Leakage control: recommendation history is built only from each user's pre-holdout rows.
- Metrics: `HR@10` and `NDCG@10`.
- Subpopulation analysis: users bucketed by train-history count into `warm` and `hot` on this dataset.

Code links:

- `pipeline/eval.py`
- `training/evaluate.py`
- `report/offline_metrics.csv`
- `report/offline_subpopulations.csv`

Overall results:

| model | HR@10 | NDCG@10 | users |
| --- | ---: | ---: | ---: |
| als | 0.3333 | 0.1667 | 3 |
| item_item | 0.3333 | 0.2103 | 3 |
| popularity | 0.3333 | 0.1667 | 3 |

Subpopulation result highlights:

- `item_item` on `warm`: `HR@10=1.0`, `NDCG@10=0.6309`.
- All models on `hot`: `HR@10=0.0`, `NDCG@10=0.0` on this small sample.

Benchmark support metrics from `report/benchmark.csv`:

| model | train_s | size_mb | p95_ms | rps |
| --- | ---: | ---: | ---: | ---: |
| popularity | 0.0016 | 0.0003 | 0.0003 | 4122314.46 |
| item_item | 0.0075 | 0.0025 | 0.0302 | 40195.55 |
| als | 0.0176 | 0.0021 | 0.0197 | 52653.79 |

## 3. Online KPI spec & results from `alpha.reco_responses`

Spec:

- Source: Kafka topic `alpha.reco_responses`.
- Proxy success definition: `status_code == 200` and `num_results >= 1` and `latency_ms <= 2000`.
- Supporting KPIs: `healthy_response_rate`, `personalized_rate`, `error_rate`, `latency_ms_p95`.

Code links:

- `pipeline/eval.py`
- `training/online_eval.py`
- `report/online_kpi_summary.csv`
- `report/online_kpi_by_model.csv`

Results:

- Responses: `6`
- Proxy success rate: `83.33%`
- Healthy response rate: `83.33%`
- Personalized rate: `50.00%`
- P95 latency: `15381 ms`
- Error rate: `16.67%`

Per-model KPI slice:

| model | responses | proxy_success_rate | personalized_rate |
| --- | ---: | ---: | ---: |
| error | 1 | 0.00 | 0.00 |
| item_item | 3 | 1.00 | 1.00 |
| popularity | 2 | 1.00 | 0.00 |

## 4. Data quality gates

Schema validation:

- Watch schema: `user_id`, `item_id`, `timestamp`
- Rate schema: `user_id`, `item_id`, `rating in [0,5]`, `timestamp`
- Recommendation-response schema: request id, user, model, num results, personalization flag, latency, status, error

Implementation links:

- `pipeline/quality.py`
- `ingestor/validator.py`
- `ingestor/consumer.py`

Drift report (`report/drift_report.csv`), comparing early vs late interaction windows:

| check | statistic | threshold | drift |
| --- | ---: | ---: | --- |
| item_distribution_tvd | 0.4464 | 0.20 | True |
| user_activity_tvd | 0.6667 | 0.20 | True |
| unique_users_delta_pct | 0.5000 | 0.20 | True |
| unique_items_delta_pct | 0.3333 | 0.20 | True |

## 5. CI/CD, tests, and repo hygiene

Workflow files:

- `.github/workflows/ci-cd.yml`: lint, tests, coverage, Docker build/push, Azure Container Apps deploy on `main`.
- `.github/workflows/probe.yml`: scheduled probe publisher.

Secrets strategy:

- Docker Hub: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
- Azure Container Apps: `AZURE_CREDENTIALS`, `AZURE_CONTAINER_APP_NAME`, `AZURE_RESOURCE_GROUP`
- Kafka/API probe secrets remain in `probe.yml`

Successful runs link:

- Repository URL: https://github.com/Padmarao2024/milestone3
- Latest successful CI/CD run URL: https://github.com/Padmarao2024/milestone3/actions/runs/24795362593
- Current run status: `test-and-quality`, `build-and-push`, and `deploy-azure-container-apps` all passed.
- Deployment status: Azure Container App `recommender-api` is running in resource group `milestones-rg` and serving `GET /health` with HTTP 200.
- Secrets configured and validated in Actions: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `AZURE_CREDENTIALS`, `AZURE_CONTAINER_APP_NAME`, and `AZURE_RESOURCE_GROUP`.

Test report:

- Command: `pytest --cov=pipeline.config --cov=pipeline.eval --cov=pipeline.quality --cov=pipeline.serve --cov=pipeline.transform --cov-report=term-missing --cov-fail-under=70`
- Result: `10 passed`, `74.68%` coverage on scoped non-ML glue modules.
- Artifact: `report/test_report.txt`

Repo hygiene updates:

- `README.md` updated for the milestone 3 architecture.
- `requirements-dev.txt`, `pytest.ini`, `ruff.toml` added.
- Runtime modules split cleanly between ingest, transform, train, serve, and eval.