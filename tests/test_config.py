from pipeline.config import EvalSettings, KafkaSettings, SnapshotSettings


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
    monkeypatch.setenv("TEAM", "omega")
    monkeypatch.setenv("KAFKA_SECURITY_PROTOCOL", "SSL")
    monkeypatch.setenv("KAFKA_SSL_CA_LOCATION", "/tmp/ca.pem")
    monkeypatch.setenv("SNAPSHOT_BASE_PATH", "s3://bucket/snapshots")
    monkeypatch.setenv("SNAPSHOT_FORMAT", "csv")
    monkeypatch.setenv("SNAPSHOT_BATCH_SIZE", "7")
    monkeypatch.setenv("ONLINE_SUCCESS_LATENCY_MS", "1500")

    kafka = KafkaSettings.from_env()
    snapshots = SnapshotSettings.from_env()
    eval_settings = EvalSettings.from_env()

    assert kafka.topic("watch") == "omega.watch"
    assert kafka.client_config("group")["security.protocol"] == "SSL"
    assert snapshots.base_path == "s3://bucket/snapshots"
    assert snapshots.file_format == "csv"
    assert snapshots.batch_size == 7
    assert eval_settings.success_latency_ms == 1500
