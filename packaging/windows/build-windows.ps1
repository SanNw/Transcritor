# Compila o transcritor.exe (PyInstaller) e o instalador Windows (Inno Setup).
# Rode a partir de uma máquina Windows com Python 3.10+ e o Inno Setup
# instalados (https://jrsoftware.org/isinfo.php).
#
# Uso (PowerShell, a partir da raiz do repositório):
#   .\packaging\windows\build-windows.ps1

$ErrorActionPreference = "Stop"

$RepoDir = (Resolve-Path "$PSScriptRoot\..\..").Path
$BackendDir = Join-Path $RepoDir "backend"

Write-Host "== Compilando binário com PyInstaller ==" -ForegroundColor Yellow
Push-Location $BackendDir
try {
    if (-not (Test-Path ".venv-build")) {
        python -m venv .venv-build
    }
    & ".venv-build\Scripts\pip.exe" install --quiet --upgrade pip
    & ".venv-build\Scripts\pip.exe" install --quiet -r requirements-desktop.txt

    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "transcritor.spec") { Remove-Item -Force "transcritor.spec" }

    & ".venv-build\Scripts\pyinstaller.exe" --name transcritor --onefile --windowed `
        --icon "..\packaging\icons\transcritor.ico" `
        qt_main.py
}
finally {
    Pop-Location
}

Write-Host "Binário gerado em $BackendDir\dist\transcritor.exe" -ForegroundColor Green

Write-Host "== Compilando o instalador com Inno Setup ==" -ForegroundColor Yellow
$Iscc = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
if (-not $Iscc) {
    $DefaultPath = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (Test-Path $DefaultPath) {
        $Iscc = $DefaultPath
    }
}

if (-not $Iscc) {
    Write-Warning "ISCC.exe (Inno Setup) não encontrado. Instale em https://jrsoftware.org/isinfo.php e rode este script de novo."
    Write-Warning "O binário já está pronto em $BackendDir\dist\transcritor.exe"
    exit 1
}

New-Item -ItemType Directory -Force -Path (Join-Path $RepoDir "dist-packages") | Out-Null
& $Iscc "$PSScriptRoot\transcritor.iss"

Write-Host "Instalador gerado em dist-packages\" -ForegroundColor Green
