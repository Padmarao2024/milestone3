import json

from confluent_kafka import Producer


def emit(producer: Producer, topic: str, payload: dict):
    producer.produce(topic, json.dumps(payload).encode("utf-8"))
    producer.flush()
