#!/bin/bash
# Generate self-signed SSL certificates for local development
# Run with sudo: sudo ./generate-certs.sh

set -e

SSL_DIR="/etc/nginx/ssl"
mkdir -p "$SSL_DIR"

echo "Generating self-signed SSL certificates for local development..."

# Pet-Friendly Vet
echo "Creating certificate for dev.petfriendlyvet.com..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/dev-petfriendlyvet.key" \
    -out "$SSL_DIR/dev-petfriendlyvet.crt" \
    -subj "/C=MX/ST=Quintana Roo/L=Puerto Morelos/O=Pet-Friendly Vet/CN=dev.petfriendlyvet.com" \
    -addext "subjectAltName=DNS:dev.petfriendlyvet.com,DNS:*.petfriendlyvet.com"

# Nestor Wheelock
echo "Creating certificate for dev.nestorwheelock.com..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/dev-nestorwheelock.key" \
    -out "$SSL_DIR/dev-nestorwheelock.crt" \
    -subj "/C=US/ST=Wisconsin/L=Madison/O=Nestor Wheelock/CN=dev.nestorwheelock.com" \
    -addext "subjectAltName=DNS:dev.nestorwheelock.com,DNS:*.nestorwheelock.com"

# Linux Remote Support
echo "Creating certificate for dev.linuxremotesupport.com..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/dev-linuxremotesupport.key" \
    -out "$SSL_DIR/dev-linuxremotesupport.crt" \
    -subj "/C=US/ST=Wisconsin/L=Madison/O=Linux Remote Support/CN=dev.linuxremotesupport.com" \
    -addext "subjectAltName=DNS:dev.linuxremotesupport.com,DNS:*.linuxremotesupport.com"

# Set permissions
chmod 644 "$SSL_DIR"/*.crt
chmod 600 "$SSL_DIR"/*.key

echo ""
echo "Certificates created in $SSL_DIR:"
ls -la "$SSL_DIR"
echo ""
echo "Done! Remember to accept the self-signed certificate warnings in your browser."
