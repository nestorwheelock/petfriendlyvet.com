#!/bin/bash
# Add development host entries to /etc/hosts
# Run with sudo: sudo ./setup-hosts.sh

set -e

HOSTS_FILE="/etc/hosts"
BACKUP_FILE="/etc/hosts.backup.$(date +%Y%m%d%H%M%S)"

echo "Backing up $HOSTS_FILE to $BACKUP_FILE..."
cp "$HOSTS_FILE" "$BACKUP_FILE"

# Check if entries already exist
if grep -q "dev.petfriendlyvet.com" "$HOSTS_FILE"; then
    echo "dev.petfriendlyvet.com already in hosts file"
else
    echo "127.0.0.1   dev.petfriendlyvet.com" >> "$HOSTS_FILE"
    echo "Added dev.petfriendlyvet.com"
fi

if grep -q "dev.nestorwheelock.com" "$HOSTS_FILE"; then
    echo "dev.nestorwheelock.com already in hosts file"
else
    echo "127.0.0.1   dev.nestorwheelock.com" >> "$HOSTS_FILE"
    echo "Added dev.nestorwheelock.com"
fi

if grep -q "dev.linuxremotesupport.com" "$HOSTS_FILE"; then
    echo "dev.linuxremotesupport.com already in hosts file"
else
    echo "127.0.0.1   dev.linuxremotesupport.com" >> "$HOSTS_FILE"
    echo "Added dev.linuxremotesupport.com"
fi

echo ""
echo "Current dev entries in /etc/hosts:"
grep -E "dev\.(petfriendlyvet|nestorwheelock|linuxremotesupport)" "$HOSTS_FILE" || echo "None found"
echo ""
echo "Done!"
