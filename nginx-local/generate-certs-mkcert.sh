#!/bin/bash
# Generate locally-trusted SSL certificates using mkcert
# These certificates are trusted by your browser without warnings
# Run with: ./generate-certs-mkcert.sh (no sudo needed)

set -e

SSL_DIR="/etc/nginx/ssl"

# Check if mkcert is installed
if ! command -v mkcert &> /dev/null; then
    echo "mkcert not found. Installing..."

    # Install dependencies
    sudo apt-get update
    sudo apt-get install -y libnss3-tools wget

    # Download mkcert
    wget -q -O /tmp/mkcert https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-amd64
    chmod +x /tmp/mkcert
    sudo mv /tmp/mkcert /usr/local/bin/mkcert

    echo "mkcert installed successfully"
fi

# Install local CA (if not already done)
echo "Installing local CA (may require password)..."
mkcert -install

# Create SSL directory
sudo mkdir -p "$SSL_DIR"

# Generate certificates
echo "Generating certificates..."
cd /tmp

# Pet-Friendly Vet
mkcert -key-file dev-petfriendlyvet.key -cert-file dev-petfriendlyvet.crt dev.petfriendlyvet.com
sudo mv dev-petfriendlyvet.key dev-petfriendlyvet.crt "$SSL_DIR/"

# Nestor Wheelock
mkcert -key-file dev-nestorwheelock.key -cert-file dev-nestorwheelock.crt dev.nestorwheelock.com
sudo mv dev-nestorwheelock.key dev-nestorwheelock.crt "$SSL_DIR/"

# Linux Remote Support
mkcert -key-file dev-linuxremotesupport.key -cert-file dev-linuxremotesupport.crt dev.linuxremotesupport.com
sudo mv dev-linuxremotesupport.key dev-linuxremotesupport.crt "$SSL_DIR/"

# Set permissions
sudo chmod 644 "$SSL_DIR"/*.crt
sudo chmod 600 "$SSL_DIR"/*.key

echo ""
echo "Certificates created in $SSL_DIR:"
ls -la "$SSL_DIR"
echo ""
echo "These certificates are trusted by your browser - no warnings!"
echo ""
echo "Restart nginx: sudo systemctl reload nginx"
