#!/bin/bash
set -e

mkdir -p /output

gcc -O2 -Wall -fPIC -shared \
    -I/opt/openssl/include \
    -o /output/libpow.so \
    /src/pow_solver.c \
    /opt/openssl/lib/libcrypto.a \
    -ldl -lpthread

echo "libpow.so built successfully"
