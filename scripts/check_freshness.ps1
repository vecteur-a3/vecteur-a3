# Chemin exact : scripts/check_freshness.ps1
# Objectif : Routine mensuelle d'audit de fraîcheur des dates last_verified (alerte dès 60 jours, seuil critique à 90 jours)
# Exécution : pwsh -File scripts/check_freshness.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Today = (Get-Date).Date
$WarningDays = 60
$MaxDays = 90
$ExpiredCount = 0
$WarningCount = 0

Write-Host "`n=== AUDIT DE FRAÎCHEUR YMYL (Alerte >= ${WarningDays}j | Critique >= ${MaxDays}j) ===" -ForegroundColor Cyan

foreach ($File in @("data/tools.json", "data/frameworks.json")) {
    if (-not (Test-Path $File)) {
        Write-Warning "Fichier introuvable : $File"
        continue
    }

    $Json = Get-Content $File -Raw -Encoding utf8 | ConvertFrom-Json
    $Items = if ($Json.PSObject.Properties.Name -contains "tools") { $Json.tools } else { $Json.frameworks }

    foreach ($Item in $Items) {
        $VerifiedDate = [datetime]::ParseExact($Item.last_verified, "yyyy-MM-dd", $null)
        $AgeDays = [math]::Floor(($Today - $VerifiedDate).TotalDays)
        $Url = if ($Item.PSObject.Properties.Name -contains "source_url") { $Item.source_url } else { $Item.official_docs_url }
        $NeedsManualCheck = if ($Item.PSObject.Properties.Name -contains "_a_verifier" -and $Item._a_verifier) { " [_a_verifier: true]" } else { "" }

        if ($AgeDays -ge $MaxDays) {
            Write-Host "[EXPIRÉ >= ${MaxDays}j]       $File -> $($Item.id) ($AgeDays jours)$NeedsManualCheck | Vérifier : $Url" -ForegroundColor Red
            $ExpiredCount++
        }
        elseif ($AgeDays -ge $WarningDays) {
            Write-Host "[À RAFRAÎCHIR >= ${WarningDays}j] $File -> $($Item.id) ($AgeDays jours)$NeedsManualCheck | Vérifier : $Url" -ForegroundColor Yellow
            $WarningCount++
        }
        else {
            Write-Host "[OK - $AgeDays j]           $File -> $($Item.id)$NeedsManualCheck (vérifié le $($Item.last_verified))" -ForegroundColor Green
        }
    }
}

Write-Host "`nBilan fraîcheur : $ExpiredCount expiré(s) (>= 90j), $WarningCount à rafraîchir (>= 60j)." -ForegroundColor Cyan
if ($ExpiredCount -gt 0) {
    exit 1
}
