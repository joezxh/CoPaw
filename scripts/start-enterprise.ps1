#Requires -Version 5.1
<#
.SYNOPSIS
    CoPaw Enterprise Management Script
.DESCRIPTION
    Manages CoPaw Enterprise services including database initialization, 
    Redis connection testing, and service lifecycle management.
.PARAMETER Action
    Action to perform: start, stop, restart, init, status
.EXAMPLE
    .\start-enterprise.ps1 -Action start
    .\start-enterprise.ps1 -Action restart
#>

param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'restart', 'init', 'status')]
    [string]$Action = 'start'
)

# ── Configuration ──────────────────────────────────────────────────────────────
$Script:ErrorActionPreference = 'Stop'

# Enterprise Configuration
$env:COPAW_ENTERPRISE_ENABLED = "true"
if (-not $env:COPAW_DB_HOST) { $env:COPAW_DB_HOST = "localhost" }
if (-not $env:COPAW_DB_PORT) { $env:COPAW_DB_PORT = "5432" }
if (-not $env:COPAW_DB_DATABASE) { $env:COPAW_DB_DATABASE = "copaw_enterprise" }
if (-not $env:COPAW_DB_USERNAME) { $env:COPAW_DB_USERNAME = "copaw" }
if (-not $env:COPAW_DB_PASSWORD) { $env:COPAW_DB_PASSWORD = "copaw123!" }
if (-not $env:COPAW_REDIS_HOST) { $env:COPAW_REDIS_HOST = "localhost" }
if (-not $env:COPAW_REDIS_PORT) { $env:COPAW_REDIS_PORT = "6379" }
if (-not $env:COPAW_JWT_SECRET) { $env:COPAW_JWT_SECRET = "super-secret-jwt-key-change-in-production" }
if (-not $env:COPAW_FIELD_ENCRYPT_KEY) { $env:COPAW_FIELD_ENCRYPT_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef" }

# Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PidFile = Join-Path $ProjectRoot ".copaw-enterprise.pid"
$LogFile = Join-Path (Join-Path $ProjectRoot "logs") "copaw-enterprise.log"

# Colors
$ColorSuccess = 'Green'
$ColorError = 'Red'
$ColorWarning = 'Yellow'
$ColorInfo = 'Cyan'

# ── Helper Functions ───────────────────────────────────────────────────────────

function Write-Success { param([string]$Message) Write-Host "✓ $Message" -ForegroundColor $ColorSuccess }
function Write-Error2 { param([string]$Message) Write-Host "✗ $Message" -ForegroundColor $ColorError }
function Write-Warning2 { param([string]$Message) Write-Host "⚠ $Message" -ForegroundColor $ColorWarning }
function Write-Info { param([string]$Message) Write-Host "ℹ $Message" -ForegroundColor $ColorInfo }

function Test-Command {
    param([string]$Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Test-PostgreSQL {
    Write-Info "Testing PostgreSQL connection..."
    $connString = "Host=$env:COPAW_DB_HOST;Port=$env:COPAW_DB_PORT;Database=$env:COPAW_DB_DATABASE;Username=$env:COPAW_DB_USERNAME;Password=$env:COPAW_DB_PASSWORD"
    
    try {
        # Try using psql if available
        if (Test-Command 'psql') {
            $result = psql -h $env:COPAW_DB_HOST -p $env:COPAW_DB_PORT -U $env:COPAW_DB_USERNAME -d $env:COPAW_DB_DATABASE -c "SELECT 1" -t -A 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "PostgreSQL connection successful"
                return $true
            }
        }
        
        # Fallback: Test with Python
        $configJson = @{
            username = $env:COPAW_DB_USERNAME
            password = $env:COPAW_DB_PASSWORD
            host = $env:COPAW_DB_HOST
            port = $env:COPAW_DB_PORT
            database = $env:COPAW_DB_DATABASE
        } | ConvertTo-Json -Compress
        
        $env:COPAW_DB_CONFIG = $configJson
        
        # Create temporary Python script file
        $tempScript = [System.IO.Path]::GetTempFileName() + ".py"
        @'
import sys
import os
import json
try:
    import asyncio
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from urllib.parse import quote_plus
    
    async def test():
        config = json.loads(os.environ.get('COPAW_DB_CONFIG', '{}'))
        db_user = config.get('username', 'copaw')
        db_pass = config.get('password', '')
        db_host = config.get('host', 'localhost')
        db_port = config.get('port', '5432')
        db_name = config.get('database', 'copaw_enterprise')
        
        encoded_pass = quote_plus(db_pass)
        url = 'postgresql+asyncpg://' + db_user + ':' + encoded_pass + '@' + db_host + ':' + db_port + '/' + db_name
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            result.scalar()
        await engine.dispose()
        return True
    
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
except Exception as e:
    print('Error: ' + str(e), file=sys.stderr)
    sys.exit(1)
'@ | Out-File -FilePath $tempScript -Encoding UTF8
        
        python $tempScript
        $exitCode = $LASTEXITCODE
        Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
        if ($exitCode -eq 0) {
            Write-Success "PostgreSQL connection successful"
            return $true
        }
        
        Write-Error2 "PostgreSQL connection failed"
        return $false
    }
    catch {
        Write-Error2 "PostgreSQL connection failed: $_"
        return $false
    }
}

function Test-Redis {
    Write-Info "Testing Redis connection..."
    
    try {
        # Try using redis-cli if available
        if (Test-Command 'redis-cli') {
            $result = redis-cli -h $env:COPAW_REDIS_HOST -p $env:COPAW_REDIS_PORT ping 2>&1
            if ($result -eq 'PONG') {
                Write-Success "Redis connection successful"
                return $true
            }
        }
        
        # Fallback: Test with Python
        $configJson = @{
            host = $env:COPAW_REDIS_HOST
            port = $env:COPAW_REDIS_PORT
        } | ConvertTo-Json -Compress
        
        $env:COPAW_REDIS_CONFIG = $configJson
        
        # Create temporary Python script file
        $tempScript = [System.IO.Path]::GetTempFileName() + ".py"
        @'
import sys
import os
import json
try:
    import redis
    config = json.loads(os.environ.get('COPAW_REDIS_CONFIG', '{}'))
    redis_host = config.get('host', 'localhost')
    redis_port = int(config.get('port', '6379'))
    r = redis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=3)
    r.ping()
    sys.exit(0)
except Exception as e:
    print('Error: ' + str(e), file=sys.stderr)
    sys.exit(1)
'@ | Out-File -FilePath $tempScript -Encoding UTF8
        
        python $tempScript
        $exitCode = $LASTEXITCODE
        Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
        if ($exitCode -eq 0) {
            Write-Success "Redis connection successful"
            return $true
        }
        
        Write-Error2 "Redis connection failed"
        return $false
    }
    catch {
        Write-Error2 "Redis connection failed: $_"
        return $false
    }
}

function Test-DatabaseInitialized {
    Write-Info "Checking if database is initialized..."
    
    $configJson = @{
        username = $env:COPAW_DB_USERNAME
        password = $env:COPAW_DB_PASSWORD
        host = $env:COPAW_DB_HOST
        port = $env:COPAW_DB_PORT
        database = $env:COPAW_DB_DATABASE
    } | ConvertTo-Json -Compress
    
    $env:COPAW_DB_CONFIG = $configJson
    
    # Create temporary Python script file
    $tempScript = [System.IO.Path]::GetTempFileName() + ".py"
    @'
import sys
import os
import json
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from urllib.parse import quote_plus

async def check():
    config = json.loads(os.environ.get('COPAW_DB_CONFIG', '{}'))
    db_user = config.get('username', 'copaw')
    db_pass = config.get('password', '')
    db_host = config.get('host', 'localhost')
    db_port = config.get('port', '5432')
    db_name = config.get('database', 'copaw_enterprise')
    
    encoded_pass = quote_plus(db_pass)
    url = 'postgresql+asyncpg://' + db_user + ':' + encoded_pass + '@' + db_host + ':' + db_port + '/' + db_name
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"))
            exists = result.scalar()
            if exists:
                result = await conn.execute(text('SELECT version_num FROM alembic_version'))
                version = result.scalar()
                print('initialized:' + str(version))
            else:
                print('not_initialized')
    except Exception as e:
        print('error:' + str(e))
    finally:
        await engine.dispose()

asyncio.run(check())
'@ | Out-File -FilePath $tempScript -Encoding UTF8
    
    # Capture stdout only, ignore stderr warnings
    $output = python $tempScript 2>$null
    $exitCode = $LASTEXITCODE
    Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
    
    if ($output -match '^initialized:(.+)$') {
        $version = $matches[1]
        Write-Success "Database already initialized (version: $version)"
        return $true
    }
    elseif ($output -match '^error:(.+)$') {
        Write-Warning2 "Database check failed: $($matches[1])"
        return $false
    }
    else {
        Write-Info "Database not initialized"
        return $false
    }
}

function Initialize-Database {
    Write-Info "Initializing database..."
    
    if (Test-DatabaseInitialized) {
        Write-Warning2 "Database already initialized, skipping migration"
        return $true
    }
    
    try {
        Set-Location $ProjectRoot
        alembic upgrade head
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database migration completed"
            return $true
        }
        else {
            Write-Error2 "Database migration failed"
            return $false
        }
    }
    catch {
        Write-Error2 "Database migration failed: $_"
        return $false
    }
}

function Create-AdminUser {
    param(
        [string]$Username = "admin",
        [string]$Password = "",
        [string]$Email = "admin@copaw.local",
        [string]$DisplayName = "Administrator"
    )
    
    Write-Info "Checking for admin user..."
    
    if (-not $Password) {
        $SecurePassword = Read-Host -Prompt "Enter admin password (min 8 characters)" -AsSecureString
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
        $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
    }
    
    if ($Password.Length -lt 8) {
        Write-Error2 "Password must be at least 8 characters"
        return $false
    }
    
    # Set environment variables for Python script
    $env:COPAW_ADMIN_USERNAME = $Username
    $env:COPAW_ADMIN_PASSWORD = $Password
    $env:COPAW_ADMIN_EMAIL = $Email
    $env:COPAW_ADMIN_DISPLAY_NAME = $DisplayName
    $env:COPAW_PROJECT_ROOT = $ProjectRoot
    
    $configJson = @{
        username = $env:COPAW_DB_USERNAME
        password = $env:COPAW_DB_PASSWORD
        host = $env:COPAW_DB_HOST
        port = $env:COPAW_DB_PORT
        database = $env:COPAW_DB_DATABASE
    } | ConvertTo-Json -Compress
    
    $env:COPAW_DB_CONFIG = $configJson
    
    # Create temporary Python script file
    $tempScript = [System.IO.Path]::GetTempFileName() + ".py"
    @'
import sys
import os
import json
import asyncio
import warnings
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from urllib.parse import quote_plus

# Suppress all warnings (including bcrypt/passlib compatibility)
warnings.filterwarnings('ignore')

async def create_admin():
    config = json.loads(os.environ.get('COPAW_DB_CONFIG', '{}'))
    db_user = config.get('username', 'copaw')
    db_pass = config.get('password', '')
    db_host = config.get('host', 'localhost')
    db_port = config.get('port', '5432')
    db_name = config.get('database', 'copaw_enterprise')
    
    encoded_pass = quote_plus(db_pass)
    url = 'postgresql+asyncpg://' + db_user + ':' + encoded_pass + '@' + db_host + ':' + db_port + '/' + db_name
    engine = create_async_engine(url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    
    username = os.environ.get('COPAW_ADMIN_USERNAME', 'admin')
    password = os.environ.get('COPAW_ADMIN_PASSWORD', '')
    email = os.environ.get('COPAW_ADMIN_EMAIL', 'admin@copaw.local')
    display_name = os.environ.get('COPAW_ADMIN_DISPLAY_NAME', 'Administrator')
    project_root = os.environ.get('COPAW_PROJECT_ROOT', '')
    
    try:
        async with Session() as session:
            # Step 1: Ensure default tenant exists
            tenant_check = await session.execute(text("SELECT id FROM sys_tenants WHERE id = 'default-tenant'"))
            if not tenant_check.scalar():
                await session.execute(text("""
                    INSERT INTO sys_tenants (id, name, domain, is_active, created_at, updated_at)
                    VALUES ('default-tenant', 'Default Tenant', 'default', true, NOW(), NOW())
                """))
                await session.flush()
            
            # Step 2: Check if admin user already exists
            result = await session.execute(text("SELECT id FROM sys_users WHERE username = '" + username + "'"))
            user_exists = result.scalar()
            
            if not user_exists:
                # Step 3: Create admin user
                if project_root:
                    sys.path.insert(0, project_root + '/src')
                from copaw.enterprise.auth_service import AuthService
                
                user = await AuthService.register(
                    session,
                    username=username,
                    password=password,
                    email=email,
                    display_name=display_name
                )
                await session.flush()
                user_id = str(user.id)
                print('created:' + user_id)
            else:
                result = await session.execute(text("SELECT id FROM sys_users WHERE username = '" + username + "'"))
                user_id = str(result.scalar())
                print('exists:' + user_id)
            
            # Step 4: Ensure admin role exists
            role_check = await session.execute(text("SELECT id FROM sys_roles WHERE name = 'admin'"))
            role_id = role_check.scalar()
            
            if not role_id:
                import uuid
                role_id = str(uuid.uuid4())
                await session.execute(text("""
                    INSERT INTO sys_roles (id, name, description, level, is_system_role, tenant_id, created_at, updated_at)
                    VALUES (:role_id, 'admin', 'System Administrator', 0, true, 'default-tenant', NOW(), NOW())
                """), {'role_id': role_id})
                await session.flush()
            
            # Step 5: Ensure admin user has admin role
            if user_id and role_id:
                user_role_check = await session.execute(text("""
                    SELECT 1 FROM sys_user_roles WHERE user_id = :user_id AND role_id = :role_id
                """), {'user_id': user_id, 'role_id': role_id})
                
                if not user_role_check.scalar():
                    await session.execute(text("""
                        INSERT INTO sys_user_roles (user_id, role_id, assigned_at, tenant_id)
                        VALUES (:user_id, :role_id, NOW(), 'default-tenant')
                    """), {'user_id': user_id, 'role_id': role_id})
                    await session.flush()
                    print('role_assigned')
            
            await session.commit()
    except Exception as e:
        print('error:' + str(e))
    finally:
        await engine.dispose()

asyncio.run(create_admin())
'@ | Out-File -FilePath $tempScript -Encoding UTF8
    
    # Use Start-Process to capture output while suppressing stderr warnings
    $outputFile = [System.IO.Path]::GetTempFileName()
    $errorFile = [System.IO.Path]::GetTempFileName()
    
    $process = Start-Process -FilePath "python" `
        -ArgumentList $tempScript `
        -RedirectStandardOutput $outputFile `
        -RedirectStandardError $errorFile `
        -NoNewWindow `
        -Wait `
        -PassThru
    
    $output = Get-Content $outputFile -Raw -ErrorAction SilentlyContinue
    $exitCode = $process.ExitCode
    
    # Show debug info
    Write-Info "Exit code: $exitCode"
    if ($output) {
        Write-Info "Output: $output"
    }
    
    # Cleanup temp files
    Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
    Remove-Item $outputFile -Force -ErrorAction SilentlyContinue
    Remove-Item $errorFile -Force -ErrorAction SilentlyContinue
    
    # Parse multi-line output from Python script
    $outputLines = $output -split "`n" | Where-Object { $_.Trim() } | ForEach-Object { $_.Trim() }
    $mainOutput = ""
    $roleAssigned = $false
    $errorMsg = ""
    
    foreach ($line in $outputLines) {
        if ($line -eq 'role_assigned') {
            $roleAssigned = $true
        }
        elseif ($line -match '^error:(.+)$') {
            $errorMsg = $matches[1]
        }
        else {
            $mainOutput = $line
        }
    }
    
    if ($mainOutput -match '^exists:([a-f0-9-]+)$') {
        $userId = $matches[1]
        Write-Warning2 "Admin user '$Username' already exists (ID: $userId)"
        if ($roleAssigned) {
            Write-Success "Admin role assigned successfully"
        }
        return $true
    }
    elseif ($mainOutput -match '^created:([a-f0-9-]+)$') {
        $userId = $matches[1]
        Write-Success "Admin user created successfully (ID: $userId)"
        Write-Info "Username: $Username"
        Write-Info "Password: ********"
        if ($roleAssigned) {
            Write-Success "Admin role assigned successfully"
        }
        return $true
    }
    elseif ($errorMsg) {
        Write-Error2 "Failed to create admin user: $errorMsg"
        return $false
    }
    else {
        Write-Error2 "Failed to create admin user"
        return $false
    }
}

function Get-CopawProcess {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile
        try {
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                return $process
            }
        }
        catch {
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        }
    }
    return $null
}

function Start-Service {
    Write-Info "Starting CoPaw Enterprise..."
    
    $process = Get-CopawProcess
    if ($process) {
        Write-Warning2 "CoPaw Enterprise is already running (PID: $($process.Id))"
        return $true
    }
    
    try {
        # Ensure logs directory exists
        $logDir = Join-Path $ProjectRoot "logs"
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        
        # Set project root environment variable
        $env:COPAW_PROJECT_ROOT = $ProjectRoot
        
        # Create temporary Python script file
        $tempScript = [System.IO.Path]::GetTempFileName() + ".py"
        @'
import sys
import os

project_root = os.environ.get('COPAW_PROJECT_ROOT', '')
if project_root:
    sys.path.insert(0, os.path.join(project_root, 'src'))

from copaw.app._app import app
import uvicorn

uvicorn.run(app, host='127.0.0.1', port=8088, log_level='info')
'@ | Out-File -FilePath $tempScript -Encoding UTF8
        
        $process = Start-Process -FilePath "python" `
            -ArgumentList $tempScript `
            -WorkingDirectory $ProjectRoot `
            -WindowStyle Hidden `
            -PassThru
        
        # Wait for service to start
        Start-Sleep -Seconds 3
        
        # Save PID
        $process.Id | Out-File -FilePath $PidFile -Encoding utf8
        
        # Clean up temp script
        Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
        
        Write-Success "CoPaw Enterprise started (PID: $($process.Id))"
        Write-Info "Access the console at: http://localhost:8088"
        return $true
    }
    catch {
        Write-Error2 "Failed to start CoPaw Enterprise: $_"
        return $false
    }
}

function Stop-Service {
    Write-Info "Stopping CoPaw Enterprise..."
    
    $process = Get-CopawProcess
    if (-not $process) {
        Write-Warning2 "CoPaw Enterprise is not running"
        return $true
    }
    
    try {
        Stop-Process -Id $process.Id -Force
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        Write-Success "CoPaw Enterprise stopped"
        return $true
    }
    catch {
        Write-Error2 "Failed to stop CoPaw Enterprise: $_"
        return $false
    }
}

function Show-Status {
    Write-Info "CoPaw Enterprise Status"
    Write-Host ("=" * 50)
    
    # Service status
    $process = Get-CopawProcess
    if ($process) {
        Write-Success "Service: Running (PID: $($process.Id))"
    }
    else {
        Write-Error2 "Service: Stopped"
    }
    
    # Database status
    if (Test-PostgreSQL) {
        if (Test-DatabaseInitialized) {
            Write-Success "Database: Connected & Initialized"
        }
        else {
            Write-Warning2 "Database: Connected but not initialized"
        }
    }
    else {
        Write-Error2 "Database: Not connected"
    }
    
    # Redis status
    if (Test-Redis) {
        Write-Success "Redis: Connected"
    }
    else {
        Write-Error2 "Redis: Not connected"
    }
    
    Write-Host ("=" * 50)
}

# ── Main Logic ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "CoPaw Enterprise Management" -ForegroundColor $ColorInfo
Write-Host ("=" * 50)

switch ($Action) {
    'init' {
        Write-Info "Initializing CoPaw Enterprise..."
        
        # Test connections
        $dbOk = Test-PostgreSQL
        $redisOk = Test-Redis
        
        if (-not $dbOk -or -not $redisOk) {
            Write-Error2 "Prerequisites check failed. Please ensure PostgreSQL and Redis are running."
            exit 1
        }
        
        # Initialize database
        if (Initialize-Database) {
            # Create admin user
            Create-AdminUser
        }
        
        Write-Success "Initialization completed"
    }
    
    'start' {
        # Check prerequisites
        $dbOk = Test-PostgreSQL
        $redisOk = Test-Redis
        
        if (-not $dbOk -or -not $redisOk) {
            Write-Error2 "Prerequisites check failed. Please ensure PostgreSQL and Redis are running."
            Write-Info "Run '.\start-enterprise.ps1 init' to initialize the database"
            exit 1
        }
        
        # Check if database is initialized
        if (-not (Test-DatabaseInitialized)) {
            Write-Warning2 "Database not initialized"
            $response = Read-Host "Do you want to initialize now? (y/n)"
            if ($response -match '^[yY]') {
                Initialize-Database
                Create-AdminUser
            }
            else {
                exit 1
            }
        }
        
        Start-Service
    }
    
    'stop' {
        Stop-Service
    }
    
    'restart' {
        Stop-Service
        Start-Sleep -Seconds 2
        Start-Service
    }
    
    'status' {
        Show-Status
    }
}

Write-Host ""
exit 0
