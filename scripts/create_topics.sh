#!/bin/bash
set -euo pipefail

if [[ -f "configs/consumer.env" && ( -z "${KAFKA_BOOTSTRAP_SERVERS:-}" || -z "${TEAM:-}" ) ]]; then
	# Load defaults for local/dev usage.
	source configs/consumer.env
fi

if [[ -z "${KAFKA_BOOTSTRAP_SERVERS:-}" || -z "${TEAM:-}" ]]; then
	echo "KAFKA_BOOTSTRAP_SERVERS and TEAM are required."
	exit 1
fi

TOPIC_PARTITIONS="${TOPIC_PARTITIONS:-3}"
TOPIC_REPLICATION_FACTOR="${TOPIC_REPLICATION_FACTOR:-1}"

TOPICS_CMD=()
if command -v kafka-topics >/dev/null 2>&1; then
	TOPICS_CMD=(kafka-topics)
elif docker ps --format '{{.Names}}' | grep -qx kafka; then
	TOPICS_CMD=(docker exec kafka /opt/bitnami/kafka/bin/kafka-topics.sh)
else
	echo "kafka-topics not found and kafka container is not running."
	exit 1
fi

CLIENT_CONFIG=""
if [[ -n "${KAFKA_SECURITY_PROTOCOL:-}" ]]; then
	CLIENT_CONFIG="/tmp/${TEAM}_kafka_client.properties"
	{
		echo "security.protocol=${KAFKA_SECURITY_PROTOCOL}"
		if [[ -n "${KAFKA_SASL_MECHANISM:-}" ]]; then
			echo "sasl.mechanism=${KAFKA_SASL_MECHANISM}"
		fi
		if [[ -n "${KAFKA_USERNAME:-}" && -n "${KAFKA_PASSWORD:-}" ]]; then
			echo "sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username=\"${KAFKA_USERNAME}\" password=\"${KAFKA_PASSWORD}\";"
		fi
		if [[ -n "${KAFKA_SSL_CA_LOCATION:-}" ]]; then
			echo "ssl.truststore.type=PEM"
			echo "ssl.truststore.location=${KAFKA_SSL_CA_LOCATION}"
		fi
		if [[ -n "${KAFKA_SSL_CERTIFICATE_LOCATION:-}" && -n "${KAFKA_SSL_KEY_LOCATION:-}" ]]; then
			echo "ssl.keystore.type=PEM"
			echo "ssl.keystore.certificate.chain=${KAFKA_SSL_CERTIFICATE_LOCATION}"
			echo "ssl.keystore.key=${KAFKA_SSL_KEY_LOCATION}"
		fi
	} > "$CLIENT_CONFIG"
fi

TOPICS=(
	"${TEAM}.watch"
	"${TEAM}.rate"
	"${TEAM}.reco_requests"
	"${TEAM}.reco_responses"
)

for topic in "${TOPICS[@]}"; do
	if [[ -n "$CLIENT_CONFIG" ]]; then
		"${TOPICS_CMD[@]}" --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" --command-config "$CLIENT_CONFIG" --create --if-not-exists --topic "$topic" --partitions "$TOPIC_PARTITIONS" --replication-factor "$TOPIC_REPLICATION_FACTOR"
	else
		"${TOPICS_CMD[@]}" --bootstrap-server "$KAFKA_BOOTSTRAP_SERVERS" --create --if-not-exists --topic "$topic" --partitions "$TOPIC_PARTITIONS" --replication-factor "$TOPIC_REPLICATION_FACTOR"
	fi
done

if [[ -n "$CLIENT_CONFIG" && -f "$CLIENT_CONFIG" ]]; then
	rm -f "$CLIENT_CONFIG"
fi

echo "Topics ensured for team: $TEAM"
