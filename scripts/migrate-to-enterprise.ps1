#Requires -Version 5.1
<#
.SYNOPSIS
    CoPaw 个人版到企业版数据迁移脚本

.DESCRIPTION
    将CoPaw个人版的数据(auth.json, Agent配置等)迁移到企业版PostgreSQL数据库。

.PARAMETER PostgresUrl
    PostgreSQL连接字符串 (必需)

.PARAMETER DryRun
    预览模式,不实际执行迁移

.PARAMETER SkipAuth
    跳过认证数据迁移

.PARAMETER SkipAgents
    跳过Agent配置迁移

.EXAMPLE
    # 预览迁移
    .\scripts\migrate-to-enterprise.ps1 -DryRun

.EXAMPLE
    # 执行迁移
    .\scripts\migrate-to-enterprise.ps1 -PostgresUrl "postgresql://user:password@localhost:5432/copaw_enterprise"

.EXAMPLE
    # 仅迁移认证数据
    .\scripts\migrate-to-enterprise.ps1 -PostgresUrl "postgresql://user:password@localhost:5432/copaw_enterprise" -SkipAgents

.NOTES
    作者: CoPaw Team
    版本: 1.0.0
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$PostgresUrl = "",

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$SkipAuth,

    [Parameter(Mandatory = $false)]
    [switch]$SkipAgents
)

# ── 颜色输出 ─────────────────────────────────────────────────────────────

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# ── 前置检查 ─────────────────────────────────────────────────────────────

Write-Host "`n" + ("=" * 80) -ForegroundColor White
Write-Host "CoPaw 个人版 → 企业版 数据迁移工具" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor White

# 检查Python环境
Write-Info "检查Python环境..."
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Error-Custom "未找到Python,请先安装Python 3.10+"
    exit 1
}

Write-Success "Python已安装: $($pythonCmd.Source)"

# 检查迁移脚本是否存在
$scriptPath = Join-Path $PSScriptRoot "migrate_personal_to_enterprise.py"
if (-not (Test-Path $scriptPath)) {
    Write-Error-Custom "迁移脚本不存在: $scriptPath"
    exit 1
}

Write-Success "迁移脚本已找到: $scriptPath"

# URL编码函数
function ConvertTo-UrlEncoded {
    param([string]$Text)
    return [System.Uri]::EscapeDataString($Text)
}

# 检查并自动编码密码中的特殊字符
if ($PostgresUrl -match 'postgresql://([^:]+):([^@]+)@(.+)') {
    $username = $matches[1]
    $password = $matches[2]
    $hostAndDb = $matches[3]
    
    # 检查密码是否包含需要编码的字符
    if ($password -match '[!@#$%^&*()+=\[\]{};:""<>?,/\\|`]') {
        Write-Warning-Custom "检测到密码中包含特殊字符,正在自动进行URL编码..."
        $encodedPassword = ConvertTo-UrlEncoded $password
        $PostgresUrl = "postgresql://${username}:${encodedPassword}@${hostAndDb}"
        Write-Success "已编码: $PostgresUrl"
    }
}

# 获取PostgreSQL连接字符串
if (-not $PostgresUrl) {
    Write-Info "`n请输入PostgreSQL连接字符串:"
    Write-Host "  格式: postgresql://用户名:密码@主机:端口/数据库名" -ForegroundColor Gray
    Write-Host "  示例: postgresql://copaw:password@localhost:5432/copaw_enterprise`n" -ForegroundColor Gray
    Write-Host "  注意: 如果密码包含特殊字符(!@#$%^&*等),请使用URL编码" -ForegroundColor Yellow
    Write-Host "    ! 编码为 %21" -ForegroundColor Gray
    Write-Host "    @ 编码为 %40" -ForegroundColor Gray
    Write-Host "    # 编码为 %23" -ForegroundColor Gray
    Write-Host "    示例: postgresql://copaw:pass%21word@localhost:5432/copaw`n" -ForegroundColor Gray
    $PostgresUrl = Read-Host "PostgreSQL URL"
}

if (-not $PostgresUrl) {
    Write-Error-Custom "PostgreSQL连接字符串不能为空"
    exit 1
}

# 确认操作
Write-Host "`n" + ("-" * 80) -ForegroundColor Yellow
Write-Host "迁移配置:" -ForegroundColor Yellow
Write-Host ("-" * 80) -ForegroundColor Yellow
Write-Host "  数据库: $PostgresUrl"
Write-Host "  预览模式: $($DryRun.IsPresent)"
Write-Host "  跳过认证: $($SkipAuth.IsPresent)"
Write-Host "  跳过Agent: $($SkipAgents.IsPresent)"
Write-Host ("-" * 80) -ForegroundColor Yellow

if (-not $DryRun.IsPresent) {
    Write-Host "`n⚠️  警告: 这将修改数据库,请确保已备份!" -ForegroundColor Red
    $confirm = Read-Host "是否继续? (输入 YES 确认)"
    if ($confirm -ne "YES") {
        Write-Info "操作已取消"
        exit 0
    }
}

# ── 执行迁移 ─────────────────────────────────────────────────────────────

Write-Host "`n开始迁移..." -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor White

# 构建Python命令参数
$pythonArgs = @($scriptPath, "--postgres-url", $PostgresUrl)

if ($DryRun.IsPresent) {
    $pythonArgs += "--dry-run"
}
if ($SkipAuth.IsPresent) {
    $pythonArgs += "--skip-auth"
}
if ($SkipAgents.IsPresent) {
    $pythonArgs += "--skip-agents"
}

# 执行Python脚本
try {
    & $pythonCmd.Source $pythonArgs
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "`n" + ("=" * 80) -ForegroundColor Green
        Write-Success "迁移完成!"
        Write-Host ("=" * 80) -ForegroundColor Green

        if ($DryRun.IsPresent) {
            Write-Host "`n💡 这是预览模式,未实际执行迁移" -ForegroundColor Yellow
            Write-Host "💡 移除 -DryRun 参数以执行实际迁移" -ForegroundColor Yellow
        } else {
            Write-Host "`n✅ 数据已成功迁移到企业版数据库!" -ForegroundColor Green
            Write-Host "`n下一步:" -ForegroundColor Cyan
            Write-Host "  1. 启动企业版服务" -ForegroundColor White
            Write-Host "  2. 使用原用户名登录系统" -ForegroundColor White
            Write-Host "  3. 验证数据完整性" -ForegroundColor White
        }
    } else {
        Write-Host "`n" + ("=" * 80) -ForegroundColor Red
        Write-Error-Custom "迁移失败 (退出码: $exitCode)"
        Write-Host ("=" * 80) -ForegroundColor Red
        exit $exitCode
    }
} catch {
    Write-Host "`n" + ("=" * 80) -ForegroundColor Red
    Write-Error-Custom "迁移过程中发生错误: $_"
    Write-Host ("=" * 80) -ForegroundColor Red
    exit 1
}
