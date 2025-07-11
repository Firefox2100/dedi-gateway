#!/bin/bash
set -e

mkdir -p /output

gcc -O2 -Wall -fPIC -shared \
    -I/opt/openssl/include \
    -L/opt/openssl/lib \
    -Wl,-Bstatic -lcrypto -Wl,-Bdynamic \
    -o /output/libpow.so \
    /src/pow_solver.c \
    -ldl -lpthread

echo "libpow.so built successfully"
