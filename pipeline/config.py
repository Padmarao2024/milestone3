from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _getenv_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value not in {None, ""} else default


def _getenv_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in {None, ""} else default


@dataclass(frozen=True)
class KafkaSettings:
    bootstrap_servers: str
    team: str
    security_protocol: str = ""
    sasl_mechanism: str = ""
    username: str = ""
    password: str = ""
    ssl_ca_location: str = ""
    ssl_certificate_location: str = ""
    ssl_key_location: str = ""

    @classmethod
    def from_env(cls) -> "KafkaSettings":
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            team=os.getenv("TEAM", "alpha"),
            security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", ""),
            sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM", ""),
            username=os.getenv("KAFKA_USERNAME", ""),
            password=os.getenv("KAFKA_PASSWORD", ""),
            ssl_ca_location=os.getenv("KAFKA_SSL_CA_LOCATION", ""),
            ssl_certificate_location=os.getenv("KAFKA_SSL_CERTIFICATE_LOCATION", ""),
            ssl_key_location=os.getenv("KAFKA_SSL_KEY_LOCATION", ""),
        )

    def topic(self, suffix: str) -> str:
        return f"{self.team}.{suffix}"

    def client_config(self, group_id: str | None = None) -> dict[str, object]:
        config: dict[str, object] = {
            "bootstrap.servers": self.bootstrap_servers,
        }
        if group_id:
            config["group.id"] = group_id
            config["auto.offset.reset"] = "earliest"
        if self.security_protocol:
            config["security.protocol"] = self.security_protocol
        if self.sasl_mechanism:
            config["sasl.mechanisms"] = self.sasl_mechanism
        if self.username and self.password:
            config["sasl.username"] = self.username
            config["sasl.password"] = self.password
        if self.ssl_ca_location:
            config["ssl.ca.location"] = self.ssl_ca_location
        if self.ssl_certificate_location:
            config["ssl.certificate.location"] = self.ssl_certificate_location
        if self.ssl_key_location:
            config["ssl.key.location"] = self.ssl_key_location
        return config


@dataclass(frozen=True)
class SnapshotSettings:
    base_path: str
    file_format: str
    batch_size: int
    high_watermark: int

    @classmethod
    def from_env(cls) -> "SnapshotSettings":
        return cls(
            base_path=os.getenv("SNAPSHOT_BASE_PATH", "data/snapshots"),
            file_format=os.getenv("SNAPSHOT_FORMAT", "parquet").lower(),
            batch_size=_getenv_int("SNAPSHOT_BATCH_SIZE", 5),
            high_watermark=_getenv_int("SNAPSHOT_HIGH_WATERMARK", 25),
        )


@dataclass(frozen=True)
class Paths:
    data_dir: Path = Path("data")
    model_dir: Path = Path("models")
    report_dir: Path = Path("report")

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"


@dataclass(frozen=True)
class EvalSettings:
    top_k: int
    success_latency_ms: int
    min_results: int
    drift_threshold: float
    online_window_hours: float

    @classmethod
    def from_env(cls) -> "EvalSettings":
        return cls(
            top_k=_getenv_int("EVAL_TOP_K", 10),
            success_latency_ms=_getenv_int("ONLINE_SUCCESS_LATENCY_MS", 2000),
            min_results=_getenv_int("ONLINE_MIN_RESULTS", 1),
            drift_threshold=_getenv_float("DRIFT_THRESHOLD", 0.20),
            online_window_hours=_getenv_float("ONLINE_WINDOW_HOURS", 24.0),
        )
