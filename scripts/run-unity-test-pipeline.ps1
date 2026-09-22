[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$UnityExe = $env:UNITY_EXE,
    [string]$UnityProjectPath = $env:UNITY_PROJECT_PATH,
    [string]$ApiKey = $env:API_ADMIN_KEY,
    [string]$TaskName = "Unity Match3 automated test",
    [ValidateRange(60, 3600)]
    [int]$UnityTimeoutSeconds = 600
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$BaseUrl = $BaseUrl.TrimEnd("/")

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    throw "ApiKey is required. Pass -ApiKey or set API_ADMIN_KEY."
}

$apiHeaders = @{ "X-API-Key" = $ApiKey }

if ([string]::IsNullOrWhiteSpace($UnityExe)) {
    throw "UnityExe is required. Pass -UnityExe or set UNITY_EXE."
}

if ([string]::IsNullOrWhiteSpace($UnityProjectPath)) {
    throw "UnityProjectPath is required. Pass -UnityProjectPath or set UNITY_PROJECT_PATH."
}

if (-not (Test-Path -LiteralPath $UnityExe -PathType Leaf)) {
    throw "Unity executable was not found: $UnityExe"
}

if (-not (Test-Path -LiteralPath $UnityProjectPath -PathType Container)) {
    throw "Unity project was not found: $UnityProjectPath"
}

$unityLockFile = Join-Path $UnityProjectPath "Temp\UnityLockfile"
if (Test-Path -LiteralPath $unityLockFile) {
    $runningUnity = @(Get-Process -Name Unity -ErrorAction SilentlyContinue)
    if ($runningUnity.Count -gt 0) {
        throw "The Unity project appears to be open. Close the Unity Editor first."
    }

    $staleLockBackup = "$unityLockFile.stale-$(Get-Date -Format 'yyyyMMdd-HHmmss').bak"
    Move-Item -LiteralPath $unityLockFile -Destination $staleLockBackup
    Write-Warning "Moved a stale Unity lock file to $staleLockBackup"
}

Write-Host "Checking the platform API at $BaseUrl ..."
$health = Invoke-RestMethod -Method Get -Uri "$BaseUrl/health"
if ($health.status -ne "ok") {
    throw "The platform health check did not return status=ok."
}

$taskBody = @{
    name = $TaskName
    test_type = "automation"
    platform = "windows"
} | ConvertTo-Json

Write-Host "Creating a Unity automation task ..."
$task = Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/test-tasks" `
    -Headers $apiHeaders `
    -ContentType "application/json" `
    -Body $taskBody

$taskId = [int]$task.id
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$resultsRoot = Join-Path $UnityProjectPath "TestResults"
$runDirectory = Join-Path $resultsRoot "pipeline-$timestamp-task-$taskId"
New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null

Write-Host "Created task $taskId. Results: $runDirectory"

$platforms = @("EditMode", "PlayMode")
$unityRuns = @()

foreach ($platform in $platforms) {
    $platformName = $platform.ToLowerInvariant()
    $resultPath = Join-Path $runDirectory "$platformName-results.xml"
    $logPath = Join-Path $runDirectory "$platformName.log"

    Write-Host "Running Unity $platform tests ..."
    $crashHandlersBefore = @(
        Get-Process -Name UnityCrashHandler64 -ErrorAction SilentlyContinue |
            ForEach-Object { $_.Id }
    )
    $unityArguments = @(
        "-batchmode"
        "-nographics"
        "-projectPath"
        $UnityProjectPath
        "-runTests"
        "-testPlatform"
        $platform
        "-testResults"
        $resultPath
        "-logFile"
        $logPath
    )

    $processStartInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $processStartInfo.FileName = $UnityExe
    $processStartInfo.UseShellExecute = $false
    $processStartInfo.CreateNoWindow = $true
    foreach ($argument in $unityArguments) {
        $processStartInfo.ArgumentList.Add($argument)
    }

    $unityProcess = [System.Diagnostics.Process]::Start($processStartInfo)
    if ($null -eq $unityProcess) {
        throw "Failed to start Unity for $platform tests."
    }

    $finishedInTime = $unityProcess.WaitForExit($UnityTimeoutSeconds * 1000)
    $timedOut = -not $finishedInTime

    if ($timedOut) {
        Write-Warning "Unity $platform exceeded the $UnityTimeoutSeconds second timeout."
        Stop-Process -Id $unityProcess.Id -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $unityProcess.Id -Timeout 10 -ErrorAction SilentlyContinue
        $unityExitCode = 124
    }
    else {
        $unityExitCode = $unityProcess.ExitCode
    }

    $newCrashHandlers = @(
        Get-Process -Name UnityCrashHandler64 -ErrorAction SilentlyContinue |
            Where-Object { $_.Id -notin $crashHandlersBefore }
    )
    foreach ($crashHandler in $newCrashHandlers) {
        Stop-Process -Id $crashHandler.Id -Force -ErrorAction SilentlyContinue
    }

    if ($timedOut -and (Test-Path -LiteralPath $unityLockFile)) {
        $remainingUnity = @(Get-Process -Name Unity -ErrorAction SilentlyContinue)
        if ($remainingUnity.Count -eq 0) {
            $staleLockBackup = "$unityLockFile.stale-$(Get-Date -Format 'yyyyMMdd-HHmmss').bak"
            Move-Item -LiteralPath $unityLockFile -Destination $staleLockBackup
            Write-Warning "Moved the timed-out Unity lock file to $staleLockBackup"
        }
    }

    if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
        throw "Unity did not create $resultPath. Check $logPath."
    }

    Write-Host "Uploading $platform XML to task $taskId ..."
    $upload = Invoke-RestMethod `
        -Method Post `
        -Uri "$BaseUrl/test-tasks/$taskId/unity-results" `
        -Headers $apiHeaders `
        -ContentType "application/xml" `
        -InFile $resultPath

    $unityRuns += [pscustomobject]@{
        platform = $platform
        unity_exit_code = $unityExitCode
        timed_out = $timedOut
        xml_path = $resultPath
        log_path = $logPath
        uploaded_result = $upload.result
        total = $upload.total
        passed = $upload.passed
        failed = $upload.failed
    }
}

Write-Host "Fetching the combined task report ..."
$report = Invoke-RestMethod `
    -Method Get `
    -Uri "$BaseUrl/test-tasks/$taskId/report" `
    -Headers $apiHeaders
$reportPath = Join-Path $runDirectory "platform-report.json"
$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $reportPath -Encoding UTF8

$reportedPlatforms = @($report.unity_results | ForEach-Object { $_.test_platform })
foreach ($platform in $platforms) {
    if ($reportedPlatforms -notcontains $platform) {
        throw "The combined report does not contain $platform results."
    }
}

Write-Host ""
Write-Host "Unity test pipeline completed for task $taskId."
$unityRuns | Format-Table platform, total, passed, failed, uploaded_result, unity_exit_code, timed_out
Write-Host "Combined report: $reportPath"

$failedRuns = @(
    $unityRuns | Where-Object {
        $_.unity_exit_code -ne 0 -or
        $_.failed -ne 0 -or
        $_.uploaded_result -ne "Passed"
    }
)

if ($failedRuns.Count -gt 0) {
    throw "One or more Unity test runs failed. See the generated logs and report."
}
