#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Build the PoW library
mkdir -p "$PROJECT_ROOT/src/dedi_gateway/data/bin"
docker build -f "$PROJECT_ROOT/scripts/Dockerfile.powlib" -t powlib-builder "$PROJECT_ROOT"
docker run --rm \
    -v "$PROJECT_ROOT/src/dedi_gateway/data/bin:/output" \
    --user "$(id -u):$(id -g)" \
    powlib-builder
