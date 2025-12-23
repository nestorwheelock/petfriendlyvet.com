# Local Nginx Development Setup

This directory contains configuration for running a local nginx reverse proxy that mirrors the production architecture.

## Why Local Nginx?

- **Same architecture as production**: nginx → Django, with SSL termination
- **Test HTTPS behavior**: CSRF, secure cookies, redirects work correctly
- **Multiple projects**: Route dev.petfriendlyvet.com, dev.nestorwheelock.com, etc.
- **No browser warnings**: Using mkcert for locally-trusted certificates

## Prerequisites

```bash
# Install nginx
sudo apt-get install nginx

# Install mkcert dependencies
sudo apt-get install libnss3-tools wget
```

## Setup Steps

### 1. Install mkcert (Locally-Trusted Certificates)

**mkcert** creates certificates that are automatically trusted by your browser - no security warnings!

```bash
# Download mkcert
wget -O mkcert https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-amd64
chmod +x mkcert
sudo mv mkcert /usr/local/bin/

# Verify installation
mkcert --version
# Expected: v1.4.4
```

### 2. Install Local Certificate Authority

This is a one-time setup that installs a local CA in your system trust store:

```bash
mkcert -install
```

This adds a root CA to:
- System trust store
- Firefox (via libnss3-tools)
- Chrome/Chromium

### 3. Generate Certificates

```bash
# Create SSL directory
sudo mkdir -p /etc/nginx/ssl

# Generate certificates for all dev domains
cd /tmp
mkcert -key-file dev-petfriendlyvet.key -cert-file dev-petfriendlyvet.crt dev.petfriendlyvet.com
mkcert -key-file dev-nestorwheelock.key -cert-file dev-nestorwheelock.crt dev.nestorwheelock.com
mkcert -key-file dev-linuxremotesupport.key -cert-file dev-linuxremotesupport.crt dev.linuxremotesupport.com

# Move to nginx ssl directory
sudo mv *.key *.crt /etc/nginx/ssl/

# Set permissions
sudo chmod 644 /etc/nginx/ssl/*.crt
sudo chmod 600 /etc/nginx/ssl/*.key
```

Or use the provided script:
```bash
./generate-certs-mkcert.sh
```

### 4. Add Host Entries

Add to `/etc/hosts`:

```
127.0.0.1   dev.petfriendlyvet.com
127.0.0.1   dev.nestorwheelock.com
127.0.0.1   dev.linuxremotesupport.com
```

Or run:
```bash
sudo ./setup-hosts.sh
```

**Verify hosts are working:**
```bash
ping -c 1 dev.petfriendlyvet.com
# Should show: PING dev.petfriendlyvet.com (127.0.0.1)
```

### 5. Install Nginx Config

```bash
# Copy the config
sudo cp local-dev.conf /etc/nginx/sites-available/local-dev
sudo ln -sf /etc/nginx/sites-available/local-dev /etc/nginx/sites-enabled/

# Remove default site (optional, prevents conflicts)
sudo rm -f /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 6. Start Django Dev Server

```bash
cd /home/nwheelo/projects/petfriendlyvet.com
python manage.py runserver 7777
```

### 7. Access Sites

Open in browser (no certificate warnings!):
- https://dev.petfriendlyvet.com
- https://dev.nestorwheelock.com
- https://dev.linuxremotesupport.com

## Port Mapping

| Site | nginx (HTTPS) | Django Dev Server |
|------|---------------|-------------------|
| petfriendlyvet | 443 | 7777 |
| nestorwheelock | 443 | 1081 |
| linuxremotesupport | 443 | 1082 |

## Troubleshooting

### Browser still shows certificate warning

1. Verify mkcert CA is installed:
   ```bash
   mkcert -install
   ```

2. Restart browser completely (not just refresh)

3. Check certificate is correct:
   ```bash
   openssl x509 -in /etc/nginx/ssl/dev-petfriendlyvet.crt -text -noout | grep Issuer
   # Should show: Issuer: O = mkcert development CA
   ```

### Firefox shows HSTS error

Firefox caches HSTS settings. Clear it:
1. Go to `about:preferences#privacy`
2. Click "Clear Data" under "Cookies and Site Data"
3. Or: `about:config` → search `network.stricttransportsecurity.preloadlist` → set false

### Connection refused

1. Check nginx is running:
   ```bash
   sudo systemctl status nginx
   ```

2. Check Django dev server is running on correct port:
   ```bash
   python manage.py runserver 7777  # petfriendlyvet
   python manage.py runserver 1081  # nestorwheelock
   python manage.py runserver 1082  # linuxremotesupport
   ```

3. Check hosts file:
   ```bash
   cat /etc/hosts | grep dev.petfriendlyvet
   ```

### Wrong site loading

Check nginx is using the local config:
```bash
sudo nginx -T | grep "server_name dev"
```

## mkcert Reference

**What is mkcert?**
- A simple tool for creating locally-trusted development certificates
- Created by Filippo Valsorda (Go security lead at Google)
- GitHub: https://github.com/FiloSottile/mkcert

**How it works:**
1. Creates a local Certificate Authority (CA)
2. Installs CA into system/browser trust stores
3. Signs certificates with that CA
4. Browsers trust the certificates because they trust the CA

**Key commands:**
```bash
# Install local CA (one-time)
mkcert -install

# Generate certificate for domains
mkcert example.com "*.example.com" localhost 127.0.0.1

# Uninstall CA (cleanup)
mkcert -uninstall

# Show CA location
mkcert -CAROOT
```

**Supported browsers:**
- Chrome / Chromium
- Firefox (requires libnss3-tools)
- Edge
- Safari (macOS)

**Security note:**
The mkcert CA private key is stored in your user profile. Do not share it. This CA can sign certificates for any domain, so keep it secure.

## Files in This Directory

| File | Purpose |
|------|---------|
| `README.md` | This documentation |
| `local-dev.conf` | Nginx configuration for local development |
| `generate-certs.sh` | Generate self-signed certs (legacy, shows warnings) |
| `generate-certs-mkcert.sh` | Generate mkcert certs (recommended, no warnings) |
| `setup-hosts.sh` | Add entries to /etc/hosts |

## Production vs Development

| Aspect | Production | Local Development |
|--------|------------|-------------------|
| SSL Certificates | Let's Encrypt | mkcert |
| Web Server | nginx + gunicorn | nginx + Django runserver |
| Port | 443 (public) | 443 (localhost only) |
| Database | PostgreSQL (Docker) | SQLite or PostgreSQL |
| Static Files | WhiteNoise | Django dev server |
