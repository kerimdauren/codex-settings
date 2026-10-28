param([switch]$Workspace, [Parameter(ValueFromRemainingArguments=$true)][string[]]$WorkspaceArgs)

$ErrorActionPreference = "Stop"

if ($Workspace) {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        $env:PATH = "$HOME\.local\bin;" + $env:PATH
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        & winget install --exact --id Git.Git --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { throw "Git installation failed" }
        $env:PATH += ";$env:ProgramFiles\Git\cmd"
    }
    & uv run --script https://raw.githubusercontent.com/kerimdauren/codex-settings/main/scripts/workspace.py setup @WorkspaceArgs
    exit $LASTEXITCODE
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required: https://docs.astral.sh/uv/getting-started/installation/"
}

$ScriptPath = Join-Path $PSScriptRoot "bootstrap.py"
& uv run --script $ScriptPath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
