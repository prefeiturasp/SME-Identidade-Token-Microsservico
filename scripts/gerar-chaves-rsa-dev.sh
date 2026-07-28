#!/bin/sh

set -e

KEYS_DIR="dev-secrets/token-ms"
PRIVATE_KEY="$KEYS_DIR/private.pem"
PUBLIC_KEY="$KEYS_DIR/public.pem"

mkdir -p "$KEYS_DIR"

if [ -f "$PRIVATE_KEY" ] && [ -f "$PUBLIC_KEY" ]; then
    echo "As chaves já existem."
    exit 0
fi

echo "Gerando chaves RSA..."

openssl genpkey \
    -algorithm RSA \
    -out "$PRIVATE_KEY" \
    -pkeyopt rsa_keygen_bits:4096

openssl rsa \
    -pubout \
    -in "$PRIVATE_KEY" \
    -out "$PUBLIC_KEY"

chmod 600 "$PRIVATE_KEY"
chmod 644 "$PUBLIC_KEY"

echo "Chaves criadas com sucesso."
