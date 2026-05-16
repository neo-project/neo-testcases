#!/usr/bin/env pwsh
# Run tests in the tests directory

Write-Host "$(Get-Date) - Running tests..."
$groups = @(
    "basics3"            # N3
    "contractmanagement" # N3 & N4
    "crypto"             # N3 & N4
    "governance3"        # N3
    "ledger"             # N3 & N4
    "notary"             # N3 & N4
    "oracle"             # N3 & N4
    "policy"             # N3 & N4
    "rolemanagement"     # N3 & N4
    "stdlib"             # N3 & N4
    "system/fee"         # N3 & N4
    "system/opcode"      # N3 & N4
    "plugins/rpcserver"  # N3 & N4
)

$selected = $groups
$skip_initial = $false
while ($args.Length -gt 0) {
    $arg = $args[0]
    switch ($arg) {
        "--groups" {
            $selected = $args[1].Split(',')
            $args = $args[2..$args.Length]
            break
        }
        "--skip-initial" {
            $skip_initial = $true
            $args = $args[1..$args.Length]
            break
        }
        default {
            Write-Host "$(Get-Date) - Unknown option: $arg"
            Write-Host "$(Get-Date) - Usage: run_tests.ps1 [--groups group1,group2,...] [--skip-initial]"
            exit 1
            break
        }
    }
}

# validate selected groups
foreach ($group in $selected) {
    if ($group -notin $groups) {
        Write-Host "$(Get-Date) - Invalid group: $group"
        exit 1
    }
}

$failures = @()
if (-not $skip_initial) {
    Write-Host "$(Get-Date) - Running initial tests..."
    python3 -B -m testcases.initial
    if ($LASTEXITCODE -ne 0) {
        Write-Host "$(Get-Date) - Failed to run initial tests"
        $failures += "initial"
    } else {
        Write-Host "$(Get-Date) - Passed initial tests"
    }
}

foreach ($group in $selected) {
    Write-Host "$(Get-Date) - Running $group tests..."

    $testFiles = Get-ChildItem -Path "testcases\$group\*.py"
    foreach ($file in $testFiles) {
        $basename = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        Write-Host "$(Get-Date) - Run $basename test..."

        try {
            $module = $group.Replace('/', '.')
            python3 -B -m "testcases.$module.$basename"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "$(Get-Date) - Failed to run $basename test"
                $failures += "$group/$basename"
            } else {
                Write-Host "$(Get-Date) - Passed $basename test"
            }
        } catch {
            Write-Host "$(Get-Date) - Failed to run $basename test: $($_.Exception.Message)"
            $failures += "$group/$basename"
        }
    }

    Write-Host "$(Get-Date) - $group tests completed"
}

Write-Host "$(Get-Date) - Tests completed"
if ($failures.Count -gt 0) {
    Write-Host "$(Get-Date) - Failed tests: $(($failures -join ", "))"
    exit 1
} else {
    Write-Host "$(Get-Date) - All tests passed"
    exit 0
}