#!/bin/bash
set -euo pipefail

# Example usage:
# IMAGE_REPO=ghcr.io/<org-or-user>/recommender-api
# IMAGE_TAG=$(git rev-parse --short HEAD)
# ./scripts/deploy_api.sh

: "${IMAGE_REPO:?Set IMAGE_REPO, e.g. ghcr.io/org/recommender-api}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE_REF="${IMAGE_REPO}:${IMAGE_TAG}"

# Build from repo root so api/Dockerfile can copy models/ and data/.
docker build -f api/Dockerfile -t "$IMAGE_REF" .

echo "Built image: $IMAGE_REF"
echo "To push to registry:"
echo "  docker push $IMAGE_REF"
echo
echo "Cloud Run example:"
echo "  gcloud run deploy recommender-api --image $IMAGE_REF --region us-central1 --allow-unauthenticated"
echo "  gcloud run services update recommender-api --region us-central1 --set-env-vars PORT=8000"
