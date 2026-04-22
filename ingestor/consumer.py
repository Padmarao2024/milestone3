# ruff: noqa: E402

import importlib
import json
import os
import sys
from pathlib import Path

from confluent_kafka import Consumer
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingestor.snapshot_writer import write_snapshot_with_format
from pipeline.config import KafkaSettings, SnapshotSettings
from pipeline.quality import BackpressureBuffer, validate_event_record

load_dotenv("configs/consumer.env")


def get_optional_redis_client():
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return None

    try:
        redis_module = importlib.import_module("redis")
    except Exception:
        print("REDIS_URL is set but redis package is not installed; cache disabled.")
        return None

    try:
        return redis_module.from_url(redis_url, decode_responses=True)
    except AttributeError:
        return redis_module.Redis.from_url(redis_url, decode_responses=True)
    except Exception as exc:
        print(f"Redis connection failed; cache disabled: {exc}")
        return None


def cache_recent_event(cache_client, event_type: str, event: dict):
    if cache_client is None:
        return
    key = f"events:{event_type}:recent"
    cache_client.lpush(key, json.dumps(event))
    cache_client.ltrim(key, 0, 99)


def write_snapshot_object_store(records, base_path: str, event_type: str, snapshot_format: str):
    if not records:
        return None
    extension = "parquet" if snapshot_format == "parquet" else "csv"
    from datetime import datetime, timezone

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
    object_path = (
        f"{base_path.rstrip('/')}/{event_type}/date={date_str}/"
        f"snapshot_{timestamp}.{extension}"
    )

    import pandas as pd

    frame = pd.DataFrame(records)
    if snapshot_format == "csv":
        frame.to_csv(object_path, index=False)
    else:
        frame.to_parquet(object_path, index=False)
    return object_path


def flush_batches(batches: dict[str, list[dict]], base_path: str, snapshot_format: str):
    for event_type, records in batches.items():
        if not records:
            continue
        if "://" in base_path:
            path = write_snapshot_object_store(records, base_path, event_type, snapshot_format)
        else:
            path = write_snapshot_with_format(records, base_path, event_type, snapshot_format)
        print(f"Wrote {event_type} snapshot to {path}")


def pause_assignments(consumer: Consumer):
    assignments = consumer.assignment()
    if assignments:
        consumer.pause(assignments)


def resume_assignments(consumer: Consumer):
    assignments = consumer.assignment()
    if assignments:
        consumer.resume(assignments)


def main():
    kafka = KafkaSettings.from_env()
    snapshots = SnapshotSettings.from_env()
    if snapshots.file_format not in {"parquet", "csv"}:
        raise ValueError("SNAPSHOT_FORMAT must be either 'parquet' or 'csv'")

    consumer = Consumer(kafka.client_config(group_id=f"{kafka.team}-ingestor"))
    cache_client = get_optional_redis_client()

    topics = [kafka.topic("watch"), kafka.topic("rate")]
    consumer.subscribe(topics)

    print(f"Connected to Kafka at {kafka.bootstrap_servers}")
    print(f"Subscribed to topics: {topics}")

    buffer = BackpressureBuffer(
        batch_size=snapshots.batch_size,
        high_watermark=snapshots.high_watermark,
    )

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Kafka error: {msg.error()}")
                continue

            try:
                event = json.loads(msg.value().decode("utf-8"))
            except Exception as e:
                print(f"Invalid JSON skipped: {e}")
                continue

            topic = msg.topic()
            event_type = "watch" if topic.endswith(".watch") else "rate"

            try:
                validated_event = validate_event_record(event_type, event)
            except Exception as exc:
                print(f"Invalid {event_type} event skipped: {exc}")
                continue

            cache_recent_event(cache_client, event_type, validated_event)
            print(f"Accepted {event_type} event: {validated_event}")
            decision = buffer.add(event_type, validated_event)
            if decision.should_pause:
                pause_assignments(consumer)
                print("Backpressure high watermark reached; paused consumer assignments.")
            if decision.batches:
                flush_batches(decision.batches, snapshots.base_path, snapshots.file_format)
            if decision.should_resume:
                resume_assignments(consumer)
                print("Backpressure relieved; resumed consumer assignments.")

    except KeyboardInterrupt:
        print("\nStopping consumer...")
        flush_batches(buffer.flush_all(), snapshots.base_path, snapshots.file_format)

    finally:
        consumer.close()
        print("Consumer closed.")


if __name__ == "__main__":
    main()