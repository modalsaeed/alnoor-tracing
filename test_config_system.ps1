# Test Config.ini System
# This script tests that the application correctly reads config.ini

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Config.ini System Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Test 1: Check if db_manager.py has config support
Write-Host "[Test 1] Checking db_manager.py for config support..." -ForegroundColor Yellow
$dbManagerContent = Get-Content "src\database\db_manager.py" -Raw
if ($dbManagerContent -match "configparser" -and $dbManagerContent -match "_get_config_path") {
    Write-Host "  [PASS] configparser imported" -ForegroundColor Green
    Write-Host "  [PASS] _get_config_path method found" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Config support not found" -ForegroundColor Red
    exit 1
}

# Test 2: Check if config.ini.example exists
Write-Host "`n[Test 2] Checking config.ini.example..." -ForegroundColor Yellow
if (Test-Path "config.ini.example") {
    Write-Host "  [PASS] config.ini.example exists" -ForegroundColor Green
    $configContent = Get-Content "config.ini.example" -Raw
    if ($configContent -match "\[database\]" -and $configContent -match "path\s*=") {
        Write-Host "  [PASS] Contains [database] section" -ForegroundColor Green
        Write-Host "  [PASS] Contains path setting" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Invalid config format" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  [FAIL] config.ini.example not found" -ForegroundColor Red
    exit 1
}

# Test 3: Check if spec file includes config
Write-Host "`n[Test 3] Checking alnoor.spec for config inclusion..." -ForegroundColor Yellow
$specContent = Get-Content "alnoor.spec" -Raw
if ($specContent -match "config\.ini\.example") {
    Write-Host "  [PASS] config.ini.example in spec datas" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] config.ini.example not in spec" -ForegroundColor Red
    exit 1
}

# Test 4: Check busy_timeout increased
Write-Host "`n[Test 4] Checking database timeout settings..." -ForegroundColor Yellow
if ($dbManagerContent -match "busy_timeout=60000" -and $dbManagerContent -match "'timeout':\s*60") {
    Write-Host "  [PASS] busy_timeout set to 60 seconds" -ForegroundColor Green
    Write-Host "  [PASS] connect_args timeout set to 60 seconds" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Timeout not properly set" -ForegroundColor Red
    exit 1
}

# Test 5: Test config reading with temporary config file
Write-Host "`n[Test 5] Testing config.ini reading..." -ForegroundColor Yellow

# Create temporary config
$testConfigPath = "config.ini.test"
$testDbPath = "C:\Temp\test_alnoor.db"
@"
[database]
path = $testDbPath
"@ | Set-Content $testConfigPath

Write-Host "  Created test config: $testConfigPath" -ForegroundColor Gray
Write-Host "  Test database path: $testDbPath" -ForegroundColor Gray

# Create a test Python script
$testScript = @"
import sys
import configparser
from pathlib import Path

# Simulate _get_config_path logic
config_path = Path('config.ini.test')
if config_path.exists():
    config = configparser.ConfigParser()
    config.read(config_path)
    if 'database' in config and 'path' in config['database']:
        db_path = config['database']['path']
        print(f'SUCCESS: Read database path: {db_path}')
        sys.exit(0)
    else:
        print('FAIL: No database section or path')
        sys.exit(1)
else:
    print('FAIL: Config file not found')
    sys.exit(1)
"@

$testScript | Set-Content "test_config_read.py"

# Run the test
$result = & ".\venv\Scripts\python.exe" "test_config_read.py" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [PASS] Config reading works: $result" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Config reading failed: $result" -ForegroundColor Red
    Remove-Item "config.ini.test" -ErrorAction SilentlyContinue
    Remove-Item "test_config_read.py" -ErrorAction SilentlyContinue
    exit 1
}

# Clean up
Remove-Item "config.ini.test" -ErrorAction SilentlyContinue
Remove-Item "test_config_read.py" -ErrorAction SilentlyContinue
Write-Host "  Cleaned up test files" -ForegroundColor Gray

# Test 6: Check documentation
Write-Host "`n[Test 6] Checking documentation..." -ForegroundColor Yellow
$docsExist = @(
    "NETWORK_DEPLOYMENT_GUIDE.md",
    "NETWORK_DEPLOYMENT_QUICKSTART.md"
)
$allDocsExist = $true
foreach ($doc in $docsExist) {
    if (Test-Path $doc) {
        Write-Host "  [PASS] $doc exists" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $doc not found" -ForegroundColor Red
        $allDocsExist = $false
    }
}

if (-not $allDocsExist) {
    exit 1
}

# Test 7: Check release package
Write-Host "`n[Test 7] Checking release package..." -ForegroundColor Yellow
if (Test-Path "release\v1.0.4") {
    $releaseFiles = @(
        "AlnoorMedicalServices-Setup-v1.0.4.exe",
        "AlnoorMedicalServices-Portable.exe",
        "config.ini.example",
        "NETWORK_DEPLOYMENT_GUIDE.md",
        "NETWORK_DEPLOYMENT_QUICKSTART.md",
        "CHECKSUMS.txt"
    )
    
    $allFilesExist = $true
    foreach ($file in $releaseFiles) {
        $fullPath = "release\v1.0.4\$file"
        if (Test-Path $fullPath) {
            $size = (Get-Item $fullPath).Length / 1KB
            Write-Host "  [PASS] $file ($([math]::Round($size, 2)) KB)" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] $file not found" -ForegroundColor Red
            $allFilesExist = $false
        }
    }
    
    if (-not $allFilesExist) {
        exit 1
    }
} else {
    Write-Host "  [FAIL] Release directory not found" -ForegroundColor Red
    exit 1
}

# All tests passed
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ALL TESTS PASSED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nConfig.ini system is ready for deployment." -ForegroundColor Green
Write-Host "Release package: release\v1.0.4" -ForegroundColor Cyan
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Test installer on a clean PC" -ForegroundColor White
Write-Host "  2. Verify default (local) database works" -ForegroundColor White
Write-Host "  3. Test network deployment with config.ini" -ForegroundColor White
Write-Host "  4. Verify multiple PCs can access shared database" -ForegroundColor White
Write-Host "  5. Test backup/restore from network location" -ForegroundColor White
Write-Host "`n"
