param(
    [string]$ZipPath = "D:\datasets\hm_raw\h-and-m-personalized-fashion-recommendations.zip",
    [string]$ProjectRoot = "D:\Desktop\bytedance",
    [int]$PollSeconds = 60
)

$ErrorActionPreference = "Stop"
$rawDir = Split-Path -Parent $ZipPath
$logPath = Join-Path $rawDir "hm_integration.log"
$runningPath = Join-Path $rawDir "hm_integration.running"
$completePath = Join-Path $rawDir "hm_integration.complete"
$failedPath = Join-Path $rawDir "hm_integration.failed"

function Write-Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
}

function Invoke-PythonStep([string]$Name, [string[]]$Arguments) {
    Write-Log "START: $Name"
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & python @Arguments >> $logPath 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    if ($exitCode -ne 0) {
        throw "$Name failed with exit code $exitCode. See $logPath"
    }
    Write-Log "DONE: $Name"
}

if (Test-Path -LiteralPath $completePath -PathType Leaf) {
    Write-Log "Integration already completed; exiting."
    exit 0
}
if (Test-Path -LiteralPath $runningPath -PathType Leaf) {
    Write-Log "Another integration watcher is already running; exiting."
    exit 0
}

try {
    Set-Content -LiteralPath $runningPath -Value $PID -Encoding ASCII
    if (Test-Path -LiteralPath $failedPath) {
        Remove-Item -LiteralPath $failedPath -Force
    }
    Write-Log "Waiting for a complete H&M ZIP: $ZipPath"

    while ($true) {
        if (Test-Path -LiteralPath $ZipPath -PathType Leaf) {
            & python -c "import sys,zipfile; p=sys.argv[1]; ok=zipfile.is_zipfile(p); z=zipfile.ZipFile(p) if ok else None; n=z.namelist() if z else []; sys.exit(0 if ok and any(x.endswith('articles.csv') for x in n) and any('/images/' in ('/'+x.replace('\\','/')) for x in n) else 1)" $ZipPath
            if ($LASTEXITCODE -eq 0) {
                break
            }
        }
        Write-Log "ZIP is still downloading; checking again in $PollSeconds seconds."
        Start-Sleep -Seconds $PollSeconds
    }

    Write-Log "ZIP central directory is readable; starting sample and integration pipeline."
    Set-Location -LiteralPath $ProjectRoot
    $sampleDir = Join-Path $ProjectRoot "backend\data\sample"
    $sampleCsv = Join-Path $sampleDir "articles_sample.csv"
    $textIndex = Join-Path $ProjectRoot "backend\data\vector_store\text"
    $imageIndex = Join-Path $ProjectRoot "backend\data\vector_store\image"
    $report = Join-Path $ProjectRoot "backend\data\vector_store\integration_report.json"

    Invoke-PythonStep "Sample 5000 products and images" @(
        "backend\scripts\sample_hm_from_zip.py",
        "--zip_path", $ZipPath,
        "--out_dir", "backend\data\sample",
        "--sample_size", "5000"
    )
    Invoke-PythonStep "Build multilingual text index" @(
        "backend\scripts\build_text_index.py",
        "--input_csv", $sampleCsv,
        "--index_dir", $textIndex,
        "--backend", "sentence-transformers",
        "--force"
    )
    Invoke-PythonStep "Build CLIP image index" @(
        "backend\scripts\build_image_index.py",
        "--input_csv", $sampleCsv,
        "--index_dir", $imageIndex,
        "--backend", "transformers-clip",
        "--device", "auto",
        "--force"
    )
    Invoke-PythonStep "Run backend regression tests" @(
        "-m", "pytest", "backend\tests", "-q"
    )
    Invoke-PythonStep "Validate real hybrid retrieval" @(
        "backend\scripts\validate_real_retrieval.py",
        "--sample_csv", $sampleCsv,
        "--text_index_dir", $textIndex,
        "--image_index_dir", $imageIndex,
        "--report_path", $report,
        "--device", "auto"
    )

    Set-Content -LiteralPath $completePath -Value (Get-Date -Format "o") -Encoding ASCII
    Write-Log "SUCCESS: H&M real-data integration completed."
    exit 0
}
catch {
    $message = $_.Exception.Message
    Set-Content -LiteralPath $failedPath -Value $message -Encoding UTF8
    Write-Log "FAILED: $message"
    exit 1
}
finally {
    if (Test-Path -LiteralPath $runningPath) {
        Remove-Item -LiteralPath $runningPath -Force
    }
}
