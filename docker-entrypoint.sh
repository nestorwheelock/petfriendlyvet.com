#!/bin/bash
set -e

# Create media directories if they don't exist
mkdir -p /app/media/pets /app/media/pet_documents /app/media/products /app/media/categories

# Execute the main command
exec "$@"
