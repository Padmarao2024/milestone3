# Alert Runbook – recommender-api

## SLOs

| Metric | Target | Measurement window |
|--------|--------|--------------------|
| Availability (uptime) | ≥ 70% | Rolling 7-day window |
| p95 latency | ≤ 500 ms | per 5-min scrape |
| Error rate | ≤ 5% | per 5-min scrape |

---

## Alert Rules

### 1. High Error Rate
**Condition:** `rate(recommend_errors_total[5m]) / rate(recommend_requests_total[5m]) > 0.05`  
**Severity:** warning  
**Action:** Check container logs (`az containerapp logs show --name recommender-api --resource-group milestones-rg --follow`). Confirm model files are present. Roll back via `/switch?model=popularity` if ALS is failing.

### 2. High Latency (p95 > 500 ms)
**Condition:** `histogram_quantile(0.95, rate(recommend_latency_seconds_bucket[5m])) > 0.5`  
**Severity:** warning  
**Action:** Check CPU/memory scaling. Increase container replicas: `az containerapp update --name recommender-api --resource-group milestones-rg --min-replicas 2`. Consider switching to lightweight `popularity` model.

### 3. API Down (health check fails)
**Condition:** `/health` returns non-200 for > 2 consecutive minutes (Azure Monitor availability test)  
**Severity:** critical  
**Action:**
1. Check container status: `az containerapp show --name recommender-api --resource-group milestones-rg --query "properties.runningStatus"`
2. Restart: `az containerapp revision restart --name recommender-api --resource-group milestones-rg --revision <latest>`
3. Redeploy from last known-good image: trigger `workflow_dispatch` on `ci-cd.yml` in GitHub Actions.

### 4. Model Stale (no retrain in > 36 hours)
**Condition:** `model_registry/latest.json` `trained_at` timestamp is > 36 hours old  
**Severity:** info  
**Action:** Trigger `workflow_dispatch` on `retrain.yml`. Check GitHub Actions run log for retrain failures.

---

## Availability Calculation

Availability is measured over the 216-hour window (72h before + 144h after submission):

```
Availability = (total_window_seconds - downtime_seconds) / total_window_seconds × 100%
```

Evidence is collected from:
- Azure Container Apps health-check probe logs
- `/metrics` → `recommend_requests_total` counter (any scrape gap = potential downtime)
- GitHub Actions retrain job `hot-swap-deploy` step success rate

Target: ≥ 70% over the 7-day window.

---

## Dashboard

**Azure Monitor** workbook configured on subscription `14578edb-773c-48a6-b8f6-a4dacc7e7af5`:
- App: `recommender-api` in `milestones-rg`
- Metrics: HTTP request count, response time (p50/p95), error rate, replica count
- External scraping of `/metrics` via Azure Monitor managed Prometheus (or UptimeRobot free tier)

For local Grafana (development):
```bash
docker run -d -p 3000:3000 grafana/grafana
# Add Prometheus datasource pointing to your /metrics endpoint
# Import dashboard JSON from report/grafana_dashboard.json
```
