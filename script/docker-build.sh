#!/usr/bin/env bash
# Build and optionally push the ml-base Docker image locally.
# Usage:
#   ./script/docker-build.sh              # build only
#   ./script/docker-build.sh --push       # build and push to Docker Hub
#
# Requires: docker, and DOCKERHUB_USERNAME env var (or set below)

set -euo pipefail

DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-}"
IMAGE_NAME="ml-base"
TAG="latest"

if [[ -z "$DOCKERHUB_USERNAME" ]]; then
    echo "ERROR: Set DOCKERHUB_USERNAME env var"
    echo "  export DOCKERHUB_USERNAME=your-username"
    exit 1
fi

FULL_TAG="$DOCKERHUB_USERNAME/$IMAGE_NAME:$TAG"
SHA_TAG="$DOCKERHUB_USERNAME/$IMAGE_NAME:$(git rev-parse --short HEAD)"

echo "=== Building $FULL_TAG ==="
docker build -t "$FULL_TAG" -t "$SHA_TAG" .

echo "=== Built successfully ==="
echo "   $FULL_TAG"
echo "   $SHA_TAG"

if [[ "${1:-}" == "--push" ]]; then
    echo "=== Pushing to Docker Hub ==="
    docker push "$FULL_TAG"
    docker push "$SHA_TAG"
    echo "=== Pushed ==="
fi
