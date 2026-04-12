#!/usr/bin/env bash
#
# CoPaw Enterprise Management Script
# Usage: ./start-enterprise.sh {start|stop|restart|init|status}
#

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Enterprise Configuration
export COPAW_ENTERPRISE_ENABLED="${COPAW_ENTERPRISE_ENABLED:-true}"
export COPAW_DB_HOST="${COPAW_DB_HOST:-localhost}"
export COPAW_DB_PORT="${COPAW_DB_PORT:-5432}"
export COPAW_DB_DATABASE="${COPAW_DB_DATABASE:-copaw_enterprise}"
export COPAW_DB_USERNAME="${COPAW_DB_USERNAME:-copaw}"
export COPAW_DB_PASSWORD="${COPAW_DB_PASSWORD:-copaw123!}"
export COPAW_REDIS_HOST="${COPAW_REDIS_HOST:-localhost}"
export COPAW_REDIS_PORT="${COPAW_REDIS_PORT:-6379}"
export COPAW_JWT_SECRET="${COPAW_JWT_SECRET:-super-secret-jwt-key-change-in-production}"
export COPAW_FIELD_ENCRYPT_KEY="${COPAW_FIELD_ENCRYPT_KEY:-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef}"

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/.copaw-enterprise.pid"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/copaw-enterprise.log"

# ── Helper Functions ───────────────────────────────────────────────────────────

write_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

write_error() {
    echo -e "${RED}✗ $1${NC}"
}

write_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

write_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

test_postgresql() {
    write_info "Testing PostgreSQL connection..."
    
    # Try using psql if available
    if check_command psql; then
        if PGPASSWORD="$COPAW_DB_PASSWORD" psql -h "$COPAW_DB_HOST" -p "$COPAW_DB_PORT" -U "$COPAW_DB_USERNAME" -d "$COPAW_DB_DATABASE" -c "SELECT 1" -t -A >/dev/null 2>&1; then
            write_success "PostgreSQL connection successful"
            return 0
        fi
    fi
    
    # Fallback: Test with Python
    if check_command python3; then
        local python_cmd="python3"
    elif check_command python; then
        local python_cmd="python"
    else
        write_error "Python not found"
        return 1
    fi
    
    if $python_cmd <<-'PYEOF'
import sys
try:
    import redis
    r = redis.Redis(host=''"$COPAW_REDIS_HOST"'', port='"$COPAW_REDIS_PORT"', socket_connect_timeout=3)
    r.ping()
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
    then
        write_success "PostgreSQL connection successful"
        return 0
    fi
    
    write_error "PostgreSQL connection failed"
    return 1
}

test_redis() {
    write_info "Testing Redis connection..."
    
    # Try using redis-cli if available
    if check_command redis-cli; then
        local result
        result=$(redis-cli -h "$COPAW_REDIS_HOST" -p "$COPAW_REDIS_PORT" ping 2>&1)
        if [ "$result" = "PONG" ]; then
            write_success "Redis connection successful"
            return 0
        fi
    fi
    
    # Fallback: Test with Python
    if check_command python3; then
        local python_cmd="python3"
    elif check_command python; then
        local python_cmd="python"
    else
        write_error "Python not found"
        return 1
    fi
    
    if $python_cmd <<-'PYEOF'
import sys
try:
    import redis
    r = redis.Redis(host=''"$COPAW_REDIS_HOST"'', port='"$COPAW_REDIS_PORT"', socket_connect_timeout=3)
    r.ping()
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
    then
        write_success "Redis connection successful"
        return 0
    fi
    
    write_error "Redis connection failed"
    return 1
}

test_database_initialized() {
    write_info "Checking if database is initialized..."
    
    if check_command python3; then
        local python_cmd="python3"
    elif check_command python; then
        local python_cmd="python"
    else
        write_error "Python not found"
        return 1
    fi
    
    local output
    output=$($python_cmd <<-'PYEOF'
import sys
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    url = f"postgresql+asyncpg://'"$COPAW_DB_USERNAME"':'"$COPAW_DB_PASSWORD"'@'"$COPAW_DB_HOST"':'"$COPAW_DB_PORT"'/'"$COPAW_DB_DATABASE"
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"))
            exists = result.scalar()
            if exists:
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                print(f"initialized:{version}")
            else:
                print("not_initialized")
    except Exception as e:
        print(f"error:{e}")
    finally:
        await engine.dispose()

asyncio.run(check())
PYEOF
    ) || true
    
    if [[ "$output" =~ ^initialized:(.+)$ ]]; then
        local version="${BASH_REMATCH[1]}"
        write_success "Database already initialized (version: $version)"
        return 0
    elif [[ "$output" =~ ^error:(.+)$ ]]; then
        write_warning "Database check failed: ${BASH_REMATCH[1]}"
        return 1
    else
        write_info "Database not initialized"
        return 1
    fi
}

initialize_database() {
    write_info "Initializing database..."
    
    if test_database_initialized; then
        write_warning "Database already initialized, skipping migration"
        return 0
    fi
    
    cd "$PROJECT_ROOT"
    if alembic upgrade head; then
        write_success "Database migration completed"
        return 0
    else
        write_error "Database migration failed"
        return 1
    fi
}

create_admin_user() {
    local username="${1:-admin}"
    local password="${2:-}"
    local email="${3:-admin@copaw.local}"
    local display_name="${4:-Administrator}"
    
    write_info "Checking for admin user..."
    
    if [ -z "$password" ]; then
        read -sp "Enter admin password (min 8 characters): " password
        echo
    fi
    
    if [ ${#password} -lt 8 ]; then
        write_error "Password must be at least 8 characters"
        return 1
    fi
    
    if check_command python3; then
        local python_cmd="python3"
    elif check_command python; then
        local python_cmd="python"
    else
        write_error "Python not found"
        return 1
    fi
    
    local output
    output=$($python_cmd <<-'PYEOF'
import sys
import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

async def create_admin():
    url = f"postgresql+asyncpg://'"$COPAW_DB_USERNAME"':'"$COPAW_DB_PASSWORD"'@'"$COPAW_DB_HOST"':'"$COPAW_DB_PORT"'/'"$COPAW_DB_DATABASE"
    engine = create_async_engine(url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    
    try:
        async with Session() as session:
            # Check if admin user already exists
            result = await session.execute(text("SELECT id FROM sys_users WHERE username = '"$username"'"))
            if result.scalar():
                print("exists")
                return
            
            # Import after session creation to avoid circular imports
            sys.path.insert(0, '"$PROJECT_ROOT"'/src)
            from copaw.enterprise.auth_service import AuthService
            
            user = await AuthService.register(
                session,
                username='"$username"',
                password='"$password"',
                email='"$email"',
                display_name='"$display_name"'
            )
            await session.commit()
            print(f"created:{user.id}")
    except Exception as e:
        print(f"error:{e}")
    finally:
        await engine.dispose()

asyncio.run(create_admin())
PYEOF
    ) || true
    
    if [ "$output" = "exists" ]; then
        write_warning "Admin user '$username' already exists"
        return 0
    elif [[ "$output" =~ ^created:(.+)$ ]]; then
        local user_id="${BASH_REMATCH[1]}"
        write_success "Admin user created successfully (ID: $user_id)"
        write_info "Username: $username"
        write_info "Password: ********"
        return 0
    elif [[ "$output" =~ ^error:(.+)$ ]]; then
        write_error "Failed to create admin user: ${BASH_REMATCH[1]}"
        return 1
    else
        write_error "Failed to create admin user"
        return 1
    fi
}

get_copaw_pid() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

start_service() {
    write_info "Starting CoPaw Enterprise..."
    
    if pid=$(get_copaw_pid); then
        write_warning "CoPaw Enterprise is already running (PID: $pid)"
        return 0
    fi
    
    # Ensure logs directory exists
    mkdir -p "$LOG_DIR"
    
    # Start CoPaw in background
    nohup "$PROJECT_ROOT/.venv/bin/python" <<-'PYEOF' > "$LOG_FILE" 2>&1 &
import sys
import os
sys.path.insert(0, os.path.join(''"$PROJECT_ROOT"'', 'src'))

os.environ['COPAW_ENTERPRISE_ENABLED'] = '"$COPAW_ENTERPRISE_ENABLED"'
os.environ['COPAW_DB_HOST'] = '"$COPAW_DB_HOST"'
os.environ['COPAW_DB_PORT'] = '"$COPAW_DB_PORT"'
os.environ['COPAW_DB_DATABASE'] = '"$COPAW_DB_DATABASE"'
os.environ['COPAW_DB_USERNAME'] = '"$COPAW_DB_USERNAME"'
os.environ['COPAW_DB_PASSWORD'] = '"$COPAW_DB_PASSWORD"'
os.environ['COPAW_REDIS_HOST'] = '"$COPAW_REDIS_HOST"'
os.environ['COPAW_REDIS_PORT'] = '"$COPAW_REDIS_PORT"'
os.environ['COPAW_JWT_SECRET'] = '"$COPAW_JWT_SECRET"'
os.environ['COPAW_FIELD_ENCRYPT_KEY'] = '"$COPAW_FIELD_ENCRYPT_KEY"'

from copaw.app._app import app
import uvicorn

uvicorn.run(app, host='127.0.0.1', port=8088, log_level='info')
PYEOF
    
    local pid=$!
    
    # Wait for service to start
    sleep 3
    
    # Check if process is still running
    if kill -0 "$pid" 2>/dev/null; then
        echo "$pid" > "$PID_FILE"
        write_success "CoPaw Enterprise started (PID: $pid)"
        write_info "Access the console at: http://localhost:8088"
        write_info "Log file: $LOG_FILE"
        return 0
    else
        write_error "Failed to start CoPaw Enterprise. Check log file: $LOG_FILE"
        return 1
    fi
}

stop_service() {
    write_info "Stopping CoPaw Enterprise..."
    
    if pid=$(get_copaw_pid); then
        if kill -TERM "$pid" 2>/dev/null; then
            # Wait for graceful shutdown
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
            
            rm -f "$PID_FILE"
            write_success "CoPaw Enterprise stopped"
            return 0
        else
            write_error "Failed to stop CoPaw Enterprise"
            return 1
        fi
    else
        write_warning "CoPaw Enterprise is not running"
        return 0
    fi
}

show_status() {
    write_info "CoPaw Enterprise Status"
    echo "=================================================="
    
    # Service status
    if pid=$(get_copaw_pid); then
        write_success "Service: Running (PID: $pid)"
    else
        write_error "Service: Stopped"
    fi
    
    # Database status
    if test_postgresql; then
        if test_database_initialized; then
            write_success "Database: Connected & Initialized"
        else
            write_warning "Database: Connected but not initialized"
        fi
    else
        write_error "Database: Not connected"
    fi
    
    # Redis status
    if test_redis; then
        write_success "Redis: Connected"
    else
        write_error "Redis: Not connected"
    fi
    
    echo "=================================================="
}

# ── Main Logic ─────────────────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}CoPaw Enterprise Management${NC}"
echo "=================================================="

case "${1:-start}" in
    init)
        write_info "Initializing CoPaw Enterprise..."
        
        # Test connections
        db_ok=true
        redis_ok=true
        test_postgresql || db_ok=false
        test_redis || redis_ok=false
        
        if [ "$db_ok" = false ] || [ "$redis_ok" = false ]; then
            write_error "Prerequisites check failed. Please ensure PostgreSQL and Redis are running."
            exit 1
        fi
        
        # Initialize database
        if initialize_database; then
            # Create admin user
            create_admin_user
        fi
        
        write_success "Initialization completed"
        ;;
    
    start)
        # Check prerequisites
        db_ok=true
        redis_ok=true
        test_postgresql || db_ok=false
        test_redis || redis_ok=false
        
        if [ "$db_ok" = false ] || [ "$redis_ok" = false ]; then
            write_error "Prerequisites check failed. Please ensure PostgreSQL and Redis are running."
            write_info "Run './start-enterprise.sh init' to initialize the database"
            exit 1
        fi
        
        # Check if database is initialized
        if ! test_database_initialized; then
            write_warning "Database not initialized"
            read -p "Do you want to initialize now? (y/n): " response
            if [[ "$response" =~ ^[yY] ]]; then
                initialize_database
                create_admin_user
            else
                exit 1
            fi
        fi
        
        start_service
        ;;
    
    stop)
        stop_service
        ;;
    
    restart)
        stop_service
        sleep 2
        start_service
        ;;
    
    status)
        show_status
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|init|status}"
        exit 1
        ;;
esac

echo ""
exit 0
