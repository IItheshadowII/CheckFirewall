<#
Script: publish_to_github.ps1
Uso: Ejecutar desde la raíz del proyecto.
 - Si tienes `gh` instalado, lo usará para crear y pushear el repo.
 - Si no, usa la variable de entorno GITHUB_TOKEN para llamar a la API de GitHub.
Ejemplo:
  PowerShell -ExecutionPolicy Bypass -File .\publish_to_github.ps1 -Owner IItheshadowII -Repo CheckFirewall
#>

param(
    [string]$Owner = "IItheshadowII",
    [string]$Repo = "CheckFirewall",
    [switch]$Private,
    [switch]$UseGh
)

function Exec([string]$cmd) {
    Write-Host ">" $cmd
    cmd /c $cmd
}

Set-Location -Path (Get-Location)

# Ensure Git is initialized
if (-not (Test-Path .git)) {
    Write-Host "Inicializando repositorio git..."
    Exec "git init"
}

# Add .gitignore if not exists (basic for Python/Node)
if (-not (Test-Path .gitignore)) {
    @(
        "__pycache__/",
        "venv/",
        "node_modules/",
        ".env",
        "dist/",
        "build/"
    ) | Out-File -FilePath .gitignore -Encoding utf8
    Write-Host "Se creó .gitignore básico."
}

Exec "git add -A"
try {
    Exec "git commit -m \"Initial commit\""
} catch {
    Write-Host "No se realizaron cambios para commitear o ya había un commit previo. Continúo..."
}

$remoteUrl = "https://github.com/$Owner/$Repo.git"

function PushRemote() {
    Exec "git branch -M main"
    Exec "git remote remove origin 2>$null || exit 0"
    Exec "git remote add origin $remoteUrl"
    Exec "git push -u origin main"
}

if ($UseGh -or (Get-Command gh -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        Write-Host "gh no está instalado, pero se forzó el modo gh. Abortando esa ruta."
    } else {
        Write-Host "Creando repositorio con GitHub CLI (gh)..."
        $pub = if ($Private) { '--private' } else { '--public' }
        Exec "gh repo create $Owner/$Repo $pub --source=. --remote=origin --push --confirm"
        Write-Host "Listo. Repo creado con gh y contenido subido (si no hubo errores).";
        exit 0
    }
}

if ($env:GITHUB_TOKEN) {
    Write-Host "Creando repositorio usando GITHUB_TOKEN mediante API..."
    $body = @{ name = $Repo; description = "Proyecto CheckFirewall"; private = ($Private -eq $true) } | ConvertTo-Json
    try {
        $resp = Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method POST -Headers @{ Authorization = "token $env:GITHUB_TOKEN"; "User-Agent" = "publish_to_github_script" } -Body $body
        Write-Host "Repositorio creado: $($resp.html_url)"
        PushRemote
        exit 0
    } catch {
        Write-Host "Error creando repo via API: $_"
        exit 1
    }
}

Write-Host "No se encontró 'gh' ni la variable de entorno GITHUB_TOKEN. Puedes instalar 'gh' o exportar GITHUB_TOKEN antes de ejecutar este script."
Write-Host "Ejemplo usando gh (recomendado): gh auth login && gh repo create IItheshadowII/CheckFirewall --public --source=. --remote=origin --push"
Write-Host "Ejemplo usando token en PowerShell: $env:GITHUB_TOKEN = 'TU_TOKEN' ; .\publish_to_github.ps1 -Owner IItheshadowII -Repo CheckFirewall"
