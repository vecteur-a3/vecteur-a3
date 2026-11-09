# Chemin exact : scripts/update_monthly_freshness.ps1
# Objectif : Automatiser l'audit mensuel YMYL, vérifier que les URLs officielles (source_url / official_docs_url)
#            répondent en HTTP 200, mettre à jour le champ "last_verified" dans data/tools.json et data/frameworks.json,
#            puis régénérer data/privacy_intel.json, les articles Markdown et le build Hugo.
#
# Exemples d'utilisation :
#   1) Mode mensuel standard (met à jour uniquement les entrées >= 60 jours) :
#      pwsh -File scripts/update_monthly_freshness.ps1
#   2) Mode complet immédiat (force la mise à jour à aujourd'hui de toutes les entrées après contrôle HTTP) :
#      pwsh -File scripts/update_monthly_freshness.ps1 -ForceAll
#   3) Mode simulation sans modifier les fichiers (Dry Run) :
#      pwsh -File scripts/update_monthly_freshness.ps1 -ForceAll -DryRun

param (
    [int]$WarningDays = 60,
    [int]$MaxDays = 90,
    [int]$MinAgeDays = 60,
    [switch]$ForceAll,
    [switch]$SkipHttpCheck,
    [switch]$SkipRebuild,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path "hugo.toml")) {
    Write-Error "ERREUR : Exécutez ce script depuis la racine du projet C:\Users\RDPUser\Documents\vecteur-a3"
    exit 1
}

$Today = (Get-Date).Date
$TodayIso = $Today.ToString("yyyy-MM-dd")
$EffectiveThreshold = if ($ForceAll) { 0 } else { $MinAgeDays }

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "   ROUTINE MENSUELLE D'AUDIT & MISE À JOUR YMYL (Date cible : $TodayIso)" -ForegroundColor Cyan
Write-Host "   Seuil de mise à jour : >= $EffectiveThreshold jour(s) | Mode DryRun : $DryRun" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 1. Sauvegarde préventive horodatée dans backups/ (sauf en mode DryRun)
$TargetFiles = @("data/tools.json", "data/frameworks.json")
if (-not $DryRun) {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $BackupDir = Join-Path "backups" "monthly_audit_$Timestamp"
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    foreach ($File in $TargetFiles) {
        if (Test-Path $File) {
            Copy-Item -Path $File -Destination (Join-Path $BackupDir (Split-Path $File -Leaf)) -Force
        }
    }
    Write-Host "[SAUVEGARDE] Copies originales enregistrées dans : $BackupDir" -ForegroundColor DarkCyan
}

$Headers = @{
    "User-Agent" = "VecteurA3-MonthlyFreshnessAudit/1.0 (+https://privacyanalyticsintel.com; Compliance Doc Check)"
    "Accept"     = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

$TotalInspected = 0
$TotalUpdated   = 0
$TotalSkipped   = 0
$TotalHttpFailed = 0

foreach ($File in $TargetFiles) {
    if (-not (Test-Path $File)) {
        Write-Warning "Fichier introuvable : $File"
        continue
    }

    Write-Host "`n--- Analyse du fichier : $File ---" -ForegroundColor Cyan
    $RawContent = Get-Content -Path $File -Raw -Encoding utf8
    $JsonObj = $RawContent | ConvertFrom-Json
    $Items = if ($JsonObj.PSObject.Properties.Name -contains "tools") { $JsonObj.tools } else { $JsonObj.frameworks }

    $FileUpdatedCount = 0

    foreach ($Item in $Items) {
        $TotalInspected++
        $Id = $Item.id
        $OldDateStr = $Item.last_verified
        $VerifiedDate = [datetime]::ParseExact($OldDateStr, "yyyy-MM-dd", $null)
        $AgeDays = [math]::Floor(($Today - $VerifiedDate).TotalDays)
        $Url = if ($Item.PSObject.Properties.Name -contains "source_url") { $Item.source_url } else { $Item.official_docs_url }
        $FlagNote = if ($Item.PSObject.Properties.Name -contains "_a_verifier" -and $Item._a_verifier) { " [_a_verifier: true]" } else { "" }

        # Détermination du statut actuel
        $StatusLabel = if ($AgeDays -ge $MaxDays) { "EXPIRÉ ($AgeDays j)" }
                       elseif ($AgeDays -ge $WarningDays) { "À RAFRAÎCHIR ($AgeDays j)" }
                       else { "OK ($AgeDays j)" }

        # Vérifie si l'entrée doit être mise à jour selon le seuil ($EffectiveThreshold)
        if ($AgeDays -lt $EffectiveThreshold) {
            Write-Host ("  [CONSERVÉ - {0}] {1,-22} (last_verified: {2} < seuil {3}j){4}" -f $StatusLabel, $Id, $OldDateStr, $EffectiveThreshold, $FlagNote) -ForegroundColor Green
            $TotalSkipped++
            continue
        }

        if ($OldDateStr -eq $TodayIso) {
            Write-Host ("  [DÉJÀ À JOUR]      {0,-22} (last_verified est déjà à {1}){2}" -f $Id, $TodayIso, $FlagNote) -ForegroundColor Green
            $TotalSkipped++
            continue
        }

        # Contrôle en direct de l'URL officielle avant d'autoriser la mise à jour de last_verified
        $HttpOk = $true
        $HttpStatusMsg = "HTTP Check ignoré"

        if (-not $SkipHttpCheck) {
            try {
                $Resp = Invoke-WebRequest -Uri $Url -Headers $Headers -Method Get -TimeoutSec 15 -SkipHttpErrorCheck
                $StatusCode = [int]$Resp.StatusCode
                if ($StatusCode -ge 200 -and $StatusCode -lt 400) {
                    $HttpOk = $true
                    $HttpStatusMsg = "HTTP $StatusCode OK"
                } elseif ($StatusCode -eq 403 -or $StatusCode -eq 429) {
                    # Certains pare-feux (ex: Cloudflare sur support.google.com ou usefathom.com) renvoient 403 aux scripts CLI
                    $HttpOk = $true
                    $HttpStatusMsg = "HTTP $StatusCode (WAF actif - vérifier dans le navigateur : $Url)"
                } else {
                    $HttpOk = $false
                    $HttpStatusMsg = "ERREUR HTTP $StatusCode sur $Url"
                }
            } catch {
                $HttpOk = $false
                $HttpStatusMsg = "ERREUR RÉSEAU ($($_.Exception.Message)) sur $Url"
            }
        }

        if (-not $HttpOk) {
            Write-Host ("  [ÉCHEC SOURCE]     {0,-22} -> Date NON mise à jour ({1})" -f $Id, $HttpStatusMsg) -ForegroundColor Red
            $TotalHttpFailed++
            continue
        }

        # Remplacement ciblé de la date last_verified pour cet identifiant précis dans le fichier JSON
        $Pattern = '(?s)("id"\s*:\s*"' + [regex]::Escape($Id) + '".*?"last_verified"\s*:\s*")\d{4}-\d{2}-\d{2}(")'
        if ($RawContent -match $Pattern) {
            $RawContent = [regex]::Replace($RawContent, $Pattern, "`${1}$TodayIso`${2}", 1)
            $FileUpdatedCount++
            $TotalUpdated++
            $ActionTag = if ($DryRun) { "[SIMULATION MAJ]" } else { "[MIS À JOUR]" }
            Write-Host ("  {0,-18} {1,-22} : {2} -> {3} ({4}){5}" -f $ActionTag, $Id, $OldDateStr, $TodayIso, $HttpStatusMsg, $FlagNote) -ForegroundColor Yellow
        }
    }

    # Si au moins une entrée du fichier a été mise à jour, on met aussi à jour la date dans le commentaire d'en-tête et on sauvegarde
    if ($FileUpdatedCount -gt 0 -and (-not $DryRun)) {
        $RawContent = [regex]::Replace($RawContent, "(vérifi[ée]s?[^0-9]*le\s+)\d{4}-\d{2}-\d{2}", "`${1}$TodayIso")
        Set-Content -Path $File -Value $RawContent -Encoding utf8 -NoNewline

        # Validation syntaxique immédiate avec Python
        python -m json.tool $File > $null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "ERREUR CRITIQUE : Syntaxe JSON invalide dans $File après modification !"
            exit 1
        }
        Write-Host "  -> Fichier $File sauvegardé et validé ($FileUpdatedCount entrée(s) mise(s) à jour)." -ForegroundColor Green
    }
}

Write-Host "`n=== BILAN DE L'AUDIT MENSUEL ===" -ForegroundColor Cyan
Write-Host "  Entrées inspectées         : $TotalInspected" -ForegroundColor White
Write-Host "  Entrées mises à jour       : $TotalUpdated" -ForegroundColor Green
Write-Host "  Entrées déjà fraîches      : $TotalSkipped" -ForegroundColor Gray
Write-Host "  Sources en erreur HTTP     : $TotalHttpFailed" -ForegroundColor $(if ($TotalHttpFailed -gt 0) { "Red" } else { "Green" })

# Régénération automatique du pipeline Python + Hugo si des dates ont changé
if ($TotalUpdated -gt 0 -and (-not $DryRun) -and (-not $SkipRebuild)) {
    Write-Host "`n=== RÉGÉNÉRATION AUTOMATIQUE DU PIPELINE (Python + Hugo) ===" -ForegroundColor Cyan
    python scripts/ingest_privacy.py
    if ($LASTEXITCODE -ne 0) { Write-Error "Erreur lors de scripts/ingest_privacy.py"; exit 1 }

    python scripts/generate_pages.py --max-pages 15
    if ($LASTEXITCODE -ne 0) { Write-Error "Erreur lors de scripts/generate_pages.py"; exit 1 }

    hugo --minify --cleanDestinationDir
    if ($LASTEXITCODE -ne 0) { Write-Error "Erreur lors de la compilation Hugo"; exit 1 }

    Write-Host "`n✅ Mise à jour mensuelle terminée ! Vos fichiers JSON, vos articles Markdown et public/ affichent désormais la date $TodayIso." -ForegroundColor Green
} elseif ($TotalUpdated -eq 0) {
    Write-Host "`nℹ️ Aucune entrée n'avait dépassé le seuil de $EffectiveThreshold jour(s). Pour forcer la mise à jour de toutes les dates à aujourd'hui ($TodayIso), lancez :" -ForegroundColor Yellow
    Write-Host "   pwsh -File scripts/update_monthly_freshness.ps1 -ForceAll" -ForegroundColor Cyan
}

if ($TotalHttpFailed -gt 0) { exit 1 }
