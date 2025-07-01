#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Build the PoW library
mkdir -p "$PROJECT_ROOT/src/dedi_gateway/data/bin"
gcc -shared -fPIC \
    -o "$PROJECT_ROOT/src/dedi_gateway/data/bin/libpow.so" \
    "$PROJECT_ROOT/src/dedi_gateway/etc/powlib/pow_solver.c" \
    -lcrypto
