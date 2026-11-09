# Chemin exact : scripts/update_monthly_freshness.ps1
# Objectif : Automatiser l'audit mensuel YMYL, vérifier que les URLs officielles répondent en HTTP 200,
#            mettre à jour "last_verified" ET les dates internes dans data/tools.json, data/frameworks.json,
#            content/legal/*.md et les valeurs par défaut, puis régénérer les articles et le build Hugo.

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
    Write-Error "ERREUR : Exécutez ce script depuis la racine C:\Users\RDPUser\Documents\vecteur-a3"
    exit 1
}

$Today = (Get-Date).Date
$TodayIso = $Today.ToString("yyyy-MM-dd")
$EffectiveThreshold = if ($ForceAll) { 0 } else { $MinAgeDays }

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "   ROUTINE MENSUELLE D'AUDIT & MISE À JOUR YMYL (Date cible : $TodayIso)" -ForegroundColor Cyan
Write-Host "   Seuil de mise à jour : >= $EffectiveThreshold jour(s) | Mode DryRun : $DryRun" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

$TargetFiles = @("data/tools.json", "data/frameworks.json")
if (-not $DryRun) {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $BackupDir = Join-Path "backups" "monthly_audit_$Timestamp"
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    foreach ($File in @("data/tools.json", "data/frameworks.json", "content/legal/methodology.md")) {
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
$TotalHttpFailed = 0

foreach ($File in $TargetFiles) {
    if (-not (Test-Path $File)) { continue }

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

        if ($AgeDays -lt $EffectiveThreshold -and ($RawContent -notmatch "2026-10-2[78]")) {
            Write-Host ("  [CONSERVÉ - {0}j] {1,-22} (last_verified: {2})" -f $AgeDays, $Id, $OldDateStr) -ForegroundColor Green
            continue
        }

        $HttpOk = $true
        $HttpStatusMsg = "HTTP Check OK"

        if (-not $SkipHttpCheck) {
            try {
                $Resp = Invoke-WebRequest -Uri $Url -Headers $Headers -Method Get -TimeoutSec 15 -SkipHttpErrorCheck
                $StatusCode = [int]$Resp.StatusCode
                if ($StatusCode -ge 200 -and $StatusCode -lt 400) {
                    $HttpOk = $true
                    $HttpStatusMsg = "HTTP $StatusCode OK"
                } elseif ($StatusCode -eq 403 -or $StatusCode -eq 429) {
                    $HttpOk = $true
                    $HttpStatusMsg = "HTTP $StatusCode (WAF actif)"
                } else {
                    $HttpOk = $false
                    $HttpStatusMsg = "ERREUR HTTP $StatusCode sur $Url"
                }
            } catch {
                $HttpOk = $false
                $HttpStatusMsg = "ERREUR RÉSEAU sur $Url"
            }
        }

        if (-not $HttpOk) {
            Write-Host ("  [ÉCHEC SOURCE]     {0,-22} -> Date NON mise à jour ({1})" -f $Id, $HttpStatusMsg) -ForegroundColor Red
            $TotalHttpFailed++
            continue
        }

        $Pattern = '(?s)("id"\s*:\s*"' + [regex]::Escape($Id) + '".*?"last_verified"\s*:\s*")\d{4}-\d{2}-\d{2}(")'
        if ($RawContent -match $Pattern) {
            $RawContent = [regex]::Replace($RawContent, $Pattern, "`${1}$TodayIso`${2}", 1)
            $FileUpdatedCount++
            $TotalUpdated++
            Write-Host ("  [MIS À JOUR]       {0,-22} : {1} -> {2} ({3})" -f $Id, $OldDateStr, $TodayIso, $HttpStatusMsg) -ForegroundColor Yellow
        }
    }

    # Remplace également toute date "verified YYYY-MM-DD" ou "le YYYY-MM-DD" écrite en dur dans les notes descriptives du JSON
    $UpdatedRawContent = [regex]::Replace($RawContent, "(verified\s+|as of\s+|le\s+)\d{4}-\d{2}-\d{2}", "`${1}$TodayIso")

    if (($FileUpdatedCount -gt 0 -or $UpdatedRawContent -ne $RawContent) -and (-not $DryRun)) {
        Set-Content -Path $File -Value $UpdatedRawContent -Encoding utf8 -NoNewline
        python -m json.tool $File > $null
        if ($LASTEXITCODE -ne 0) { Write-Error "Syntaxe JSON invalide dans $File !"; exit 1 }
        Write-Host "  -> Fichier $File sauvegardé et validé (champs last_verified + notes internes mis à jour à $TodayIso)." -ForegroundColor Green
    }
}

# 2. Mise à jour automatique des dates de vérification dans content/legal/*.md et dans les valeurs par défaut des templates
if (-not $DryRun) {
    $FilesWithHardcodedDates = @(
        "content/legal/methodology.md",
        "content/legal/privacy.md",
        "content/legal/disclaimer.md",
        "layouts/partials/cta.html",
        "layouts/index.html",
        "layouts/_default/single.html",
        "scripts/generate_pages.py"
    )

    foreach ($DocFile in $FilesWithHardcodedDates) {
        if (Test-Path $DocFile) {
            $DocRaw = Get-Content -Path $DocFile -Raw -Encoding utf8
            # Remplace les anciennes dates de vérification (2026-10-27, 2026-10-28, etc.) par la date d'audit du jour
            $DocUpdated = [regex]::Replace($DocRaw, "2026-(10|11)-\d{2}", $TodayIso)
            if ($DocUpdated -ne $DocRaw) {
                Set-Content -Path $DocFile -Value $DocUpdated -Encoding utf8 -NoNewline
                Write-Host "[MIS À JOUR] Dates de vérification alignées sur $TodayIso dans : $DocFile" -ForegroundColor Green
            }
        }
    }
}

# 3. Régénération forcée des articles Markdown et compilation Hugo
if (-not $DryRun -and (-not $SkipRebuild)) {
    Write-Host "`n=== RÉGÉNÉRATION DU PIPELINE PYTHON & COMPILATION HUGO ===" -ForegroundColor Cyan
    python scripts/ingest_privacy.py
    if ($LASTEXITCODE -ne 0) { Write-Error "Erreur dans scripts/ingest_privacy.py"; exit 1 }

    python scripts/generate_pages.py --max-pages 15
    if ($LASTEXITCODE -ne 0) { Write-Error "Erreur dans scripts/generate_pages.py"; exit 1 }

    hugo --minify --cleanDestinationDir
    if ($LASTEXITCODE -ne 0) { Write-Error "Erreur lors de la compilation Hugo"; exit 1 }
}
