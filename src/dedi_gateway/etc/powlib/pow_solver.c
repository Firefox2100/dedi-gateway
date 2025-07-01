#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <openssl/sha.h>

#define MAX_DIFFICULTY 256
#define MAX_ITERATIONS 1000000000ULL

static int check_difficulty(const unsigned char *hash, int difficulty) {
    int full_bytes = difficulty / 8;
    int remaining_bits = difficulty % 8;

    for (int i = 0; i < full_bytes; ++i) {
        if (hash[i] != 0x00)
            return 0;
    }

    if (remaining_bits) {
        unsigned char mask = 0xFF << (8 - remaining_bits);
        if ((hash[full_bytes] & mask) != 0x00)
            return 0;
    }

    return 1;
}

int solve_pow(const char *nonce, int difficulty, unsigned long long *result) {
    if (!nonce || difficulty < 1 || difficulty > MAX_DIFFICULTY)
        return 1;

    char buffer[512];
    unsigned char hash[SHA256_DIGEST_LENGTH];

    for (unsigned long long counter = 0; counter < MAX_ITERATIONS; ++counter) {
        int len = snprintf(buffer, sizeof(buffer), "%s%llu", nonce, counter);
        if (len < 0 || len >= sizeof(buffer)) return 1;

        SHA256((unsigned char *)buffer, len, hash);

        if (check_difficulty(hash, difficulty)) {
            *result = counter;
            return 0;
        }
    }

    return 1;  // No solution found
}
