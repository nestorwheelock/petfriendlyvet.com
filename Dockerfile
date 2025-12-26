# Stage 1: Build Rust components
FROM rust:1.82-slim-bookworm as rust-builder

WORKDIR /rust

# Copy Rust source
COPY rust/Cargo.toml rust/Cargo.lock* ./
COPY rust/scc-license ./scc-license

# Build release binaries
RUN cargo build --release

# Stage 2: Python application
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Copy Rust binaries from builder
COPY --from=rust-builder /rust/target/release/scc-license /app/rust/target/release/
COPY --from=rust-builder /rust/target/release/scc-license-generate /app/rust/target/release/

# Install Python dependencies
COPY requirements/base.txt requirements/production.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy application code
COPY --chown=app:app . .

# Create media directories with proper ownership
RUN mkdir -p /app/media/pets /app/media/pet_documents /app/media/products /app/media/categories \
    && chown -R app:app /app/media

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Switch to app user
USER app

# Expose port 7777
EXPOSE 7777

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7777/health/ || exit 1

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7777", "--workers", "4", "config.wsgi:application"]
