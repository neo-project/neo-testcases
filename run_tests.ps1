# Run tests in the tests directory

Write-Host "$(Get-Date) - Running tests..."

$groups = @(
    "basics"
)

foreach ($group in $groups) {
    Write-Host "$(Get-Date) - Running $group tests..."

    $testFiles = Get-ChildItem -Path "testcases\$group\*.py"
    foreach ($file in $testFiles) {
        $basename = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        Write-Host "$(Get-Date) - Run $basename test..."

        try {
            python3 -B -m "testcases.$group.$basename"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "$(Get-Date) - Failed to run $basename test"
            } else {
                Write-Host "$(Get-Date) - Passed $basename test"
            }
        } catch {
            Write-Host "$(Get-Date) - Failed to run $basename test: $($_.Exception.Message)"
        }
    }

    Write-Host "$(Get-Date) - $group tests completed"
}

Write-Host "$(Get-Date) - Tests completed"
