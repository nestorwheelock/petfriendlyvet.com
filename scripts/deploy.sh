#!/bin/bash
# Deploy script for Django sites
# Usage: ./scripts/deploy.sh [command] [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load configuration
source "$SCRIPT_DIR/deploy.conf"

# Derive container name from project directory
PROJECT_NAME="$(basename "$PROJECT_DIR")"
# Remove .com suffix and convert to container-friendly name
CONTAINER_PREFIX="${PROJECT_NAME%.com}"
CONTAINER_PREFIX="${CONTAINER_PREFIX//./-}"
WEB_CONTAINER="${CONTAINER_PREFIX}-web-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

ssh_cmd() {
    python3 -c "
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('108.61.224.251', username='root', password='$REMOTE_PASSWORD', timeout=30)
stdin, stdout, stderr = client.exec_command('$1', timeout=${2:-300})
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('STDERR:', err)
client.close()
"
}

sftp_put() {
    local src="$1"
    local dst="$2"
    python3 -c "
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('108.61.224.251', username='root', password='$REMOTE_PASSWORD', timeout=30)
sftp = client.open_sftp()
sftp.put('$src', '$dst')
sftp.close()
client.close()
print('Uploaded: $src -> $dst')
"
}

sftp_get() {
    local src="$1"
    local dst="$2"
    python3 -c "
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('108.61.224.251', username='root', password='$REMOTE_PASSWORD', timeout=30)
sftp = client.open_sftp()
sftp.get('$src', '$dst')
sftp.close()
client.close()
print('Downloaded: $src -> $dst')
"
}

# =============================================================================
# Commands
# =============================================================================

cmd_status() {
    log_info "Checking production status..."
    ssh_cmd "cd $REMOTE_PATH && docker compose -f docker-compose.prod.yml ps"
    echo ""
    log_info "Testing site response..."
    # Use DEPLOY_URL which includes SCRIPT_NAME if set
    local check_url="${DEPLOY_URL:-$SITE_URL}"
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$check_url" 2>/dev/null || echo "000")
    if [ "$status" = "200" ]; then
        log_success "Site responding: $check_url (HTTP $status)"
    else
        log_error "Site issue: $check_url (HTTP $status)"
    fi
}

cmd_logs() {
    log_info "Tailing production logs..."
    ssh_cmd "docker logs $WEB_CONTAINER --tail 50 -f" 60
}

cmd_db_pull() {
    log_info "Pulling database from production..."

    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/prod_${timestamp}.sql"

    # Export from production
    log_info "Exporting production database..."
    ssh_cmd "docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME" 600 > "$backup_file"

    log_success "Database exported to: $backup_file"

    # Import to local
    log_info "Importing to local database..."
    docker exec -i $LOCAL_DB_CONTAINER psql -U $LOCAL_DB_USER -d $DB_NAME < "$backup_file"

    log_success "Database synced from production to local"
}

cmd_db_push() {
    log_info "Pushing database to production..."
    log_warning "This will REPLACE the production database!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Aborted."
        return
    fi

    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/local_${timestamp}.sql"

    # Export from local
    log_info "Exporting local database..."
    docker exec $LOCAL_DB_CONTAINER pg_dump -U $LOCAL_DB_USER $DB_NAME > "$backup_file"

    # Backup production first
    log_info "Backing up production database..."
    local prod_backup="$BACKUP_DIR/prod_backup_${timestamp}.sql"
    ssh_cmd "docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME" 600 > "$prod_backup"
    log_success "Production backup: $prod_backup"

    # Upload and import
    log_info "Uploading to server..."
    sftp_put "$backup_file" "/tmp/db_import.sql"

    log_info "Importing to production..."
    ssh_cmd "docker exec $DB_CONTAINER psql -U bruno -c 'DROP DATABASE IF EXISTS $DB_NAME;'"
    ssh_cmd "docker exec $DB_CONTAINER psql -U bruno -c 'CREATE DATABASE $DB_NAME OWNER $DB_USER;'"
    ssh_cmd "docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME < /tmp/db_import.sql"
    ssh_cmd "rm /tmp/db_import.sql"

    log_success "Database pushed to production"
}

cmd_media_pull() {
    log_info "Pulling media from production..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local media_tar="/tmp/media_prod_${timestamp}.tar.gz"

    # Create tarball on server
    log_info "Creating media archive on server..."
    ssh_cmd "docker exec $WEB_CONTAINER tar -czf /tmp/media.tar.gz -C /app media && docker cp $WEB_CONTAINER:/tmp/media.tar.gz /root/media_export.tar.gz"

    # Download
    log_info "Downloading media (this may take a while)..."
    sftp_get "/root/media_export.tar.gz" "$media_tar"

    # Extract locally
    log_info "Extracting to local Docker container..."
    docker cp "$media_tar" ${LOCAL_DB_CONTAINER%_db_1}_web_1:/tmp/media.tar.gz
    docker exec ${LOCAL_DB_CONTAINER%_db_1}_web_1 tar -xzf /tmp/media.tar.gz -C /app/

    # Cleanup
    ssh_cmd "rm /root/media_export.tar.gz"
    rm "$media_tar"

    log_success "Media synced from production to local"
}

cmd_media_push() {
    log_info "Pushing media to production..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local media_tar="/tmp/media_local_${timestamp}.tar.gz"

    # Create tarball from local Docker
    log_info "Creating media archive from local..."
    docker exec ${LOCAL_DB_CONTAINER%_db_1}_web_1 tar -czf /tmp/media.tar.gz -C /app media
    docker cp ${LOCAL_DB_CONTAINER%_db_1}_web_1:/tmp/media.tar.gz "$media_tar"

    local size=$(du -h "$media_tar" | cut -f1)
    log_info "Uploading media ($size)..."
    sftp_put "$media_tar" "/root/media_import.tar.gz"

    # Extract on server
    log_info "Extracting to production..."
    ssh_cmd "docker cp /root/media_import.tar.gz $WEB_CONTAINER:/tmp/ && docker exec $WEB_CONTAINER tar -xzf /tmp/media.tar.gz -C /app/"
    ssh_cmd "rm /root/media_import.tar.gz"

    # Cleanup
    rm "$media_tar"

    log_success "Media pushed to production"
}

cmd_optimize() {
    log_info "Running media optimization..."
    python3 "$SCRIPT_DIR/optimize_media.py" "$@"
}

cmd_code() {
    log_info "Pushing code to production..."

    # Build exclude args
    local exclude_args=""
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        exclude_args="$exclude_args --exclude='$pattern'"
    done

    # Create tarball
    log_info "Creating code archive..."
    local code_tar="/tmp/code_deploy.tar.gz"
    cd "$PROJECT_DIR"
    eval tar -czf "$code_tar" $exclude_args .

    local size=$(du -h "$code_tar" | cut -f1)
    log_info "Uploading code ($size)..."
    sftp_put "$code_tar" "/root/code_deploy.tar.gz"

    # Deploy on server
    log_info "Deploying on server..."
    ssh_cmd "cd $REMOTE_PATH && rm -rf /tmp/deploy_backup && cp -r . /tmp/deploy_backup"
    ssh_cmd "cd $REMOTE_PATH && tar -xzf /root/code_deploy.tar.gz"
    ssh_cmd "rm /root/code_deploy.tar.gz"

    # Rebuild container
    log_info "Rebuilding container..."
    ssh_cmd "cd $REMOTE_PATH && docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d --build" 300

    # Run migrations
    log_info "Running migrations..."
    ssh_cmd "docker exec $WEB_CONTAINER python manage.py migrate" 120

    # Collect static
    log_info "Collecting static files..."
    ssh_cmd "docker exec $WEB_CONTAINER python manage.py collectstatic --noinput" 60

    # Cleanup
    rm "$code_tar"

    # Verify
    sleep 3
    cmd_status
}

cmd_push() {
    log_info "Full deployment: code + media + database..."

    # Run tests first
    log_info "Running tests..."
    cd "$PROJECT_DIR"
    if ! python -m pytest --tb=short -q 2>/dev/null; then
        log_warning "Tests failed or not configured. Continue anyway? (yes/no)"
        read -p "> " confirm
        if [ "$confirm" != "yes" ]; then
            log_info "Aborted."
            return
        fi
    fi

    # Optimize media
    cmd_optimize --new-only

    # Push code
    cmd_code

    # Push media
    cmd_media_push

    log_success "Full deployment complete!"
    cmd_status
}

cmd_rollback() {
    log_info "Rolling back to previous deployment..."
    ssh_cmd "cd $REMOTE_PATH && rm -rf . && cp -r /tmp/deploy_backup/* ."
    ssh_cmd "cd $REMOTE_PATH && docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d --build" 300
    log_success "Rollback complete"
    cmd_status
}

cmd_help() {
    echo "Usage: ./scripts/deploy.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  push          Full deployment (code + media + restart)"
    echo "  code          Push code only, rebuild container"
    echo "  media-push    Push local media to production"
    echo "  media-pull    Pull production media to local"
    echo "  db-push       Push local database to production"
    echo "  db-pull       Pull production database to local"
    echo "  optimize      Run media optimization locally"
    echo "  status        Check production status"
    echo "  logs          Tail production logs"
    echo "  rollback      Revert to previous deployment"
    echo "  help          Show this help"
    echo ""
    echo "Examples:"
    echo "  ./scripts/deploy.sh status"
    echo "  ./scripts/deploy.sh db-pull"
    echo "  ./scripts/deploy.sh optimize --all"
    echo "  ./scripts/deploy.sh push"
}

# =============================================================================
# Main
# =============================================================================

case "${1:-help}" in
    push)
        cmd_push
        ;;
    code)
        cmd_code
        ;;
    media-push|media)
        cmd_media_push
        ;;
    media-pull)
        cmd_media_pull
        ;;
    db-push)
        cmd_db_push
        ;;
    db-pull)
        cmd_db_pull
        ;;
    optimize)
        shift
        cmd_optimize "$@"
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    rollback)
        cmd_rollback
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        log_error "Unknown command: $1"
        cmd_help
        exit 1
        ;;
esac
