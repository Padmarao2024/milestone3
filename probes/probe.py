import os
import time
import uuid

import requests
from confluent_kafka import Producer
from dotenv import load_dotenv
from producer import emit

load_dotenv("configs/probe.env")

API_URL = os.getenv("API_URL", "http://localhost:8000/recommend")
TEAM = os.getenv("TEAM", "team")


def build_producer() -> Producer:
    conf = {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", ""),
    }

    security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "")
    if security_protocol:
        conf["security.protocol"] = security_protocol

    ssl_ca = os.getenv("KAFKA_SSL_CA_LOCATION", "")
    ssl_cert = os.getenv("KAFKA_SSL_CERTIFICATE_LOCATION", "")
    ssl_key = os.getenv("KAFKA_SSL_KEY_LOCATION", "")
    if ssl_ca:
        conf["ssl.ca.location"] = ssl_ca
    if ssl_cert:
        conf["ssl.certificate.location"] = ssl_cert
    if ssl_key:
        conf["ssl.key.location"] = ssl_key

    username = os.getenv("KAFKA_USERNAME", "")
    password = os.getenv("KAFKA_PASSWORD", "")
    if username and password:
        conf.update({
            "security.protocol": os.getenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL"),
            "sasl.mechanisms": os.getenv("KAFKA_SASL_MECHANISM", "PLAIN"),
            "sasl.username": username,
            "sasl.password": password,
        })
    return Producer(conf)


def run_once(producer: Producer):
    request_id = str(uuid.uuid4())
    user_id = os.getenv("PROBE_USER_ID", "user_123")
    k = int(os.getenv("PROBE_K", "10"))

    req_event = {
        "request_id": request_id,
        "timestamp": time.time(),
        "user_id": user_id,
        "k": k,
    }
    emit(producer, f"{TEAM}.reco_requests", req_event)

    start = time.time()
    status_code = 599
    model = "error"
    num_results = 0
    personalized = False
    error = None

    try:
        resp = requests.get(API_URL, params={"user_id": user_id, "k": k}, timeout=20)
        status_code = resp.status_code
        body = resp.json()
        model = body.get("model", "unknown")
        num_results = len(body.get("recommendations", []))
        personalized = bool(body.get("personalized", False))
    except Exception as exc:
        error = str(exc)

    latency_ms = int((time.time() - start) * 1000)
    resp_event = {
        "request_id": request_id,
        "timestamp": time.time(),
        "user_id": user_id,
        "model": model,
        "num_results": num_results,
        "personalized": personalized,
        "latency_ms": latency_ms,
        "status_code": status_code,
        "error": error,
    }
    emit(producer, f"{TEAM}.reco_responses", resp_event)


def main():
    producer = build_producer()
    interval_seconds = int(os.getenv("PROBE_INTERVAL_SECONDS", "0"))
    max_runs = int(os.getenv("PROBE_MAX_RUNS", "1"))

    if interval_seconds <= 0:
        run_once(producer)
        return

    run_count = 0
    while max_runs <= 0 or run_count < max_runs:
        run_once(producer)
        run_count += 1
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
