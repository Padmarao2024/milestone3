# Submission Evidence Pack

## 1. Kafka verification

Managed Kafka bootstrap:

- recommender-kafka-fau-2e4c.k.aivencloud.com:26251

Security config used (SSL client cert):

- security.protocol=SSL
- ssl.ca.location=./padmarao_ca.pem
- ssl.certificate.location=./padmarao_service.cert
- ssl.key.location=./padmarao_service.key

Verified topic list from `kcat -L`:

- alpha.watch (2 partitions)
- alpha.rate (2 partitions)
- alpha.reco_requests (2 partitions)
- alpha.reco_responses (2 partitions)

Validation excerpt captured during Kafka verification:

```text
$ kcat -L -b recommender-kafka-fau-2e4c.k.aivencloud.com:26251 ...
   alpha.watch (2 partitions)
   alpha.rate (2 partitions)
   alpha.reco_requests (2 partitions)
   alpha.reco_responses (2 partitions)
```

Produce/consume verification:

- Produced events to all 4 topics with kcat.
- Consumed latest records successfully from all 4 topics.
- Observed result summary from verification run:

```text
OK: alpha.watch
OK: alpha.rate
OK: alpha.reco_requests
OK: alpha.reco_responses
```

## 2. Data snapshot description

Snapshot pathing and versioning are implemented in `ingestor/consumer.py`.

Path shape:

- <base_path>/<event_type>/date=YYYY-MM-DD/snapshot_HHMMSS.<parquet|csv>

Examples:

- data/snapshots/watch/date=2026-04-18/snapshot_164009.parquet
- s3://your-bucket/reco-snapshots/rate/date=2026-04-18/snapshot_164012.csv

Notes:

- `SNAPSHOT_BASE_PATH` controls local vs object-store target.
- `SNAPSHOT_FORMAT` supports parquet or csv.

## 3. Model comparison outputs

Scripts:

- training/evaluate.py
- training/benchmark.py

Generated outputs:

- report/offline_metrics.csv
- report/benchmark.csv

Metric definition triplets:

- HR@K: hit if held-out item appears in top-K recommendations.
- NDCG@K: discounted gain based on held-out item rank in top-K.
- Latency/Throughput: p50/p95 latency and requests-per-second over repeated local inference calls.

Model comparison table:

| model | HR@10 | NDCG@10 | train_s | size_mb | p50_ms | p95_ms | rps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| popularity | 0.00 | 0.00 | 0.028 | 0.0002 | 0.0002 | 0.0003 | 4318220.92 |
| item_item | 0.00 | 0.00 | 0.032 | 0.0039 | 0.0308 | 0.0340 | 36495.94 |
| als | 0.00 | 0.00 | 0.048 | 0.0020 | 0.0197 | 0.0213 | 46847.18 |

## 4. Live API + Docker + registry

Live API URL:

- https://recommender-api-latest-m099.onrender.com/recommend

Health check:

- https://recommender-api-latest-m099.onrender.com/health

Docker artifacts:

- Dockerfile: api/Dockerfile
- Image: docker.io/padmarao369/recommender-api:latest
- Digest: sha256:b8ecaa224470bbe5829bafcc3d20a6c3d33c6de68791c482190905eefee321cb

## 5. Ops log (last 24h)

Window (UTC):

- start=2026-04-17T16:49:25.297314+00:00
- end=2026-04-18T16:49:25.297314+00:00

Counters from alpha.reco_requests and alpha.reco_responses:

- reco_requests_24h=9
- reco_responses_24h=8
- personalized_responses_24h=1
- personalized_pct_24h=12.50

Telemetry reliability note:

- Probe script now emits a response event even when API call fails or times out.
- One older request in this 24h window did not have a response event before the reliability fix.

## 6. Reproducibility notes

Run order:

1. Create and verify topics:
   - `TOPIC_PARTITIONS=2 TOPIC_REPLICATION_FACTOR=2 bash scripts/create_topics.sh`
   - `bash scripts/verify_kafka.sh`
2. Run ingestor:
   - `python ingestor/consumer.py`
3. Train/evaluate/benchmark:
   - `bash scripts/train_all.sh`
4. Build and publish API image:
   - `docker buildx build --platform linux/amd64 -f api/Dockerfile -t padmarao369/recommender-api:latest --push .`
5. Run probes:
   - `python probes/probe.py`

GitHub Actions probe cron is configured in `.github/workflows/probe.yml`.
