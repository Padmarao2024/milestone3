#!/bin/bash
set -euo pipefail

if [[ -f "configs/consumer.env" && ( -z "${KAFKA_BOOTSTRAP_SERVERS:-}" || -z "${TEAM:-}" ) ]]; then
	source configs/consumer.env
fi

if [[ -z "${KAFKA_BOOTSTRAP_SERVERS:-}" || -z "${TEAM:-}" ]]; then
	echo "KAFKA_BOOTSTRAP_SERVERS and TEAM are required."
	exit 1
fi

KC_ARGS=(-b "$KAFKA_BOOTSTRAP_SERVERS")
if [[ -n "${KAFKA_SECURITY_PROTOCOL:-}" ]]; then
	KC_ARGS+=(-X "security.protocol=$KAFKA_SECURITY_PROTOCOL")
fi
if [[ -n "${KAFKA_SASL_MECHANISM:-}" ]]; then
	KC_ARGS+=(-X "sasl.mechanisms=$KAFKA_SASL_MECHANISM")
fi
if [[ -n "${KAFKA_USERNAME:-}" && -n "${KAFKA_PASSWORD:-}" ]]; then
	KC_ARGS+=(
		-X "sasl.username=$KAFKA_USERNAME"
		-X "sasl.password=$KAFKA_PASSWORD"
	)
fi
if [[ -n "${KAFKA_SSL_CA_LOCATION:-}" ]]; then
	KC_ARGS+=(-X "ssl.ca.location=$KAFKA_SSL_CA_LOCATION")
fi
if [[ -n "${KAFKA_SSL_CERTIFICATE_LOCATION:-}" ]]; then
	KC_ARGS+=(-X "ssl.certificate.location=$KAFKA_SSL_CERTIFICATE_LOCATION")
fi
if [[ -n "${KAFKA_SSL_KEY_LOCATION:-}" ]]; then
	KC_ARGS+=(-X "ssl.key.location=$KAFKA_SSL_KEY_LOCATION")
fi

KCAT_CMD=()
if command -v kcat >/dev/null 2>&1; then
	KCAT_CMD=(kcat)
elif docker network inspect recommender-project_default >/dev/null 2>&1; then
	KCAT_CMD=(docker run --rm --network recommender-project_default edenhill/kcat:1.7.1)
	if [[ "$KAFKA_BOOTSTRAP_SERVERS" == "localhost:9092" ]]; then
		KC_ARGS=(-b "kafka:9094" "${KC_ARGS[@]:2}")
	fi
else
	echo "kcat not found and docker network recommender-project_default is unavailable."
	exit 1
fi

echo "Listing Kafka metadata..."
"${KCAT_CMD[@]}" "${KC_ARGS[@]}" -L

TOPICS=(
	"${TEAM}.watch"
	"${TEAM}.rate"
	"${TEAM}.reco_requests"
	"${TEAM}.reco_responses"
)

echo "Verifying required topics..."
for topic in "${TOPICS[@]}"; do
	if "${KCAT_CMD[@]}" "${KC_ARGS[@]}" -L -t "$topic" >/dev/null 2>&1; then
		echo "OK: $topic"
	else
		echo "MISSING: $topic"
		exit 1
	fi
done

echo "Sampling watch/rate streams if records exist..."
"${KCAT_CMD[@]}" "${KC_ARGS[@]}" -t "${TEAM}.watch" -C -o beginning -c 5 -e || true
"${KCAT_CMD[@]}" "${KC_ARGS[@]}" -t "${TEAM}.rate" -C -o beginning -c 5 -e || true
