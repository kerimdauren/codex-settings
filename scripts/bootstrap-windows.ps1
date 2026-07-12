$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required: https://docs.astral.sh/uv/getting-started/installation/"
}

$ScriptPath = Join-Path $PSScriptRoot "bootstrap.py"
& uv run --script $ScriptPath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
