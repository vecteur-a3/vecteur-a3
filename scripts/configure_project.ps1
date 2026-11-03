# Chemin exact : scripts/configure_project.ps1
# Rôle : Mettre à jour le domaine, l'e-mail et les liens d'affiliation dans tous les fichiers existants sans jamais reconstruire un fichier de mémoire.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ==============================================================================
# 1. BLOC DE CONFIGURATION CENTRALISÉ (MODIFIEZ VOS VALEURS ICI)
# ==============================================================================
$Config = @{
    # --- DOMAINE & CONTACT ---
    # Dès que vous achetez votre nom de domaine (~10 $/an), remplacez ces deux valeurs :
    NewDomain        = "ton-domaine-privacy-a3.com"
    NewContactEmail  = "contact@ton-domaine-privacy-a3.com"

    # Si $false : supprime temporairement static/CNAME pour tester sur https://<pseudo>.github.io/<repo>/
    KeepCnameFile    = $true

    # --- LIENS D'AFFILIATION (OU URLS OFFICIELLES PROPRES EN ATTENDANT L'APPROBATION) ---
    # Tant que votre candidature n'est pas approuvée, laissez les URLs officielles propres ci-dessous.
    # Dès que vous recevez un identifiant affilié, collez l'URL affiliée complète ici et relancez le script !
    AffiliateUrls = @{
        SimpleAnalytics = "https://www.simpleanalytics.com/"
        Plausible       = "https://plausible.io/"
        Fathom          = "https://usefathom.com/"
        PiwikPro        = "https://piwik.pro/"
        Matomo          = "https://matomo.org/"
    }
}

# ==============================================================================
# 2. SAUVEGARDE PRÉVENTIVE HORODATÉE
# ==============================================================================
if (-not (Test-Path "hugo.toml")) {
    Write-Error "ERREUR : hugo.toml est introuvable. Exécutez ce script depuis C:\Users\RDPUser\Documents\vecteur-a3"
    exit 1
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path "backups" "config_update_$Timestamp"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$TargetFiles = @(
    "hugo.toml",
    "static/CNAME",
    "layouts/partials/head.html",
    "layouts/partials/cta.html",
    "content/legal/privacy.md",
    "content/legal/methodology.md",
    "content/legal/disclaimer.md",
    "data/tools.json",
    "scripts/generate_pages.py"
)

foreach ($RelPath in $TargetFiles) {
    if (Test-Path $RelPath) {
        $DestPath = Join-Path $BackupDir ($RelPath -replace '[\\/]', '_')
        Copy-Item -Path $RelPath -Destination $DestPath -Force
    }
}
Write-Host "[SAUVEGARDE] Copie de sécurité créée dans : $BackupDir" -ForegroundColor Cyan

# ==============================================================================
# 3. FONCTION DE REMPLACEMENT CHIRURGICAL SUR LES FICHIERS EXISTANTS
# ==============================================================================
function Update-FileInPlace {
    param (
        [string]$FilePath,
        [hashtable]$Replacements
    )
    if (-not (Test-Path $FilePath)) { return }

    $OriginalContent = Get-Content -Path $FilePath -Raw -Encoding utf8
    $UpdatedContent = $OriginalContent
    $ChangeCount = 0

    foreach ($Pattern in $Replacements.Keys) {
        $ReplacementValue = $Replacements[$Pattern]
        $MatchesFound = [regex]::Matches($UpdatedContent, $Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase).Count
        if ($MatchesFound -gt 0) {
            $UpdatedContent = [regex]::Replace(
                $UpdatedContent,
                $Pattern,
                $ReplacementValue,
                [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
            )
            $ChangeCount += $MatchesFound
        }
    }

    if ($UpdatedContent -ne $OriginalContent) {
        Set-Content -Path $FilePath -Value $UpdatedContent -Encoding utf8 -NoNewline
        Write-Host "[MIS À JOUR] $FilePath ($ChangeCount remplacement(s) effectué(s))" -ForegroundColor Green
    } else {
        Write-Host "[DÉJÀ PROPRE] $FilePath" -ForegroundColor Gray
    }
}

# ==============================================================================
# 4. APPLICATION DES REMPLACEMENTS (DOMAINE, E-MAIL & LIENS D'AFFILIATION)
# ==============================================================================
$OldDomainPattern = "(ton-domaine-privacy-a3\.com|ton-futur-domaine\.com|example\.com)"
$OldEmailPattern  = "contact@(ton-domaine-privacy-a3\.com|ton-futur-domaine\.com|example\.com)"

# A. Mise à jour de hugo.toml
Update-FileInPlace -FilePath "hugo.toml" -Replacements @{
    "baseURL\s*=\s*['""]https?://[^'""]+['""]"          = "baseURL = 'https://$($Config.NewDomain)/'"
    "contact_email\s*=\s*['""][^'""]+['""]"             = "contact_email = '$($Config.NewContactEmail)'"
    "analytics_domain\s*=\s*['""][^'""]*['""]"          = "analytics_domain = '$($Config.NewDomain)'"
    $OldEmailPattern                                    = $Config.NewContactEmail
    $OldDomainPattern                                   = $Config.NewDomain
}

# B. Mise à jour de static/CNAME
if ($Config.KeepCnameFile) {
    Set-Content -Path "static/CNAME" -Value $Config.NewDomain -Encoding utf8 -NoNewline
    Write-Host "[MIS À JOUR] static/CNAME -> $($Config.NewDomain)" -ForegroundColor Green
} else {
    if (Test-Path "static/CNAME") {
        Remove-Item -Path "static/CNAME" -Force
        Write-Host "[SUPPRIMÉ TEMPORAIREMENT] static/CNAME (mode test sur URL .github.io)" -ForegroundColor Yellow
    }
}

# C. Mise à jour des pages légales
foreach ($LegalFile in @("content/legal/privacy.md", "content/legal/methodology.md", "content/legal/disclaimer.md")) {
    Update-FileInPlace -FilePath $LegalFile -Replacements @{
        $OldEmailPattern  = $Config.NewContactEmail
        $OldDomainPattern = $Config.NewDomain
    }
}

# D. Remplacement des URLs affiliées (gère à la fois ?ref=A_REMPLACER et /ref/A_REMPLACER)
$AffiliateReplacements = @{
    "https?://(www\.)?simpleanalytics\.com/[^\s'""\)]*(A_REMPLACER|TON_ID_AFFILIE)[^\s'""\)]*" = $Config.AffiliateUrls.SimpleAnalytics
    "https?://(www\.)?plausible\.io/[^\s'""\)]*(A_REMPLACER|TON_ID_AFFILIE)[^\s'""\)]*"        = $Config.AffiliateUrls.Plausible
    "https?://(www\.)?usefathom\.com/[^\s'""\)]*(A_REMPLACER|TON_ID_AFFILIE)[^\s'""\)]*"       = $Config.AffiliateUrls.Fathom
    "https?://(www\.)?piwik\.pro/[^\s'""\)]*(A_REMPLACER|TON_ID_AFFILIE)[^\s'""\)]*"           = $Config.AffiliateUrls.PiwikPro
    "https?://(www\.)?matomo\.org/[^\s'""\)]*(A_REMPLACER|TON_ID_AFFILIE)[^\s'""\)]*"          = $Config.AffiliateUrls.Matomo
}

foreach ($AffFile in @("data/tools.json", "scripts/generate_pages.py", "layouts/partials/cta.html")) {
    Update-FileInPlace -FilePath $AffFile -Replacements $AffiliateReplacements
}

# ==============================================================================
# 5. VALIDATION JSON, RÉGÉNÉRATION DES ARTICLES PYTHON ET REBUILD HUGO
# ==============================================================================
Write-Host "`n=== 5. VALIDATION SYNTAXIQUE ET RÉGÉNÉRATION DU SITE ===" -ForegroundColor Cyan
python -m json.tool data/tools.json > $null
if ($LASTEXITCODE -ne 0) { Write-Error "Erreur de syntaxe dans data/tools.json !"; exit 1 }
Write-Host "[OK] data/tools.json est syntaxiquement valide." -ForegroundColor Green

python scripts/ingest_privacy.py
if ($LASTEXITCODE -ne 0) { Write-Error "Erreur dans scripts/ingest_privacy.py"; exit 1 }

Get-ChildItem -Path "content/posts" -Filter "*.md" -ErrorAction SilentlyContinue | ForEach-Object {
    Update-FileInPlace -FilePath $_.FullName -Replacements $AffiliateReplacements
}

python scripts/generate_pages.py --max-pages 15
if ($LASTEXITCODE -ne 0) { Write-Error "Erreur dans scripts/generate_pages.py"; exit 1 }

hugo --minify --cleanDestinationDir
if ($LASTEXITCODE -ne 0) { Write-Error "Erreur lors de la compilation Hugo"; exit 1 }

# ==============================================================================
# 6. AUDIT AUTOMATIQUE POST-REMPLACEMENT
# ==============================================================================
Write-Host "`n=== 6. CONTRÔLE FINAL SUR LES FICHIERS SOURCES ET COMPILÉS ===" -ForegroundColor Cyan

$SourceHits = Select-String -Path "data/tools.json", "scripts/generate_pages.py", "layouts/partials/cta.html", "layouts/partials/head.html" -Pattern "A_REMPLACER|TON_ID_AFFILIE"
if ($null -eq $SourceHits) {
    Write-Host "✅ ZÉRO marqueur A_REMPLACER / TON_ID_AFFILIE dans data/tools.json, generate_pages.py, cta.html et head.html !" -ForegroundColor Green
} else {
    Write-Host "❌ Marqueurs restants dans les fichiers sources :" -ForegroundColor Red
    $SourceHits | ForEach-Object { Write-Host "  -> $($_.Path):$($_.LineNumber) : $($_.Line.Trim())" -ForegroundColor Yellow }
}

$PublicHtml = Get-ChildItem -Path "public" -Filter "*.html" -Recurse
$RemainingPlaceholders = Select-String -Path $PublicHtml.FullName -Pattern "A_REMPLACER|TON_ID_AFFILIE|localhost:1313|betterstack|statuscake|reditus"
if ($null -eq $RemainingPlaceholders) {
    Write-Host "✅ ZÉRO marqueur factice ni résidu A1 dans public/ !" -ForegroundColor Green
} else {
    Write-Host "❌ ATTENTION : Marqueurs restants dans public/ :" -ForegroundColor Red
    $RemainingPlaceholders | ForEach-Object { Write-Host "  -> $($_.Path):$($_.LineNumber) : $($_.Line.Trim())" -ForegroundColor Yellow }
}

$PostHtmlFiles = Get-ChildItem -Path "public" -Filter "index.html" -Recurse |
    Where-Object { $_.FullName -notmatch "\\public\\(index\.html|legal\\|categories\\|tags\\)" }

$ValidArticles = 0
foreach ($Post in $PostHtmlFiles) {
    $RawHtml = Get-Content $Post.FullName -Raw -Encoding utf8
    if (($RawHtml -match 'rel="sponsored nofollow"') -and ($RawHtml -match 'Not Legal Advice') -and ($RawHtml -match 'rel=canonical|rel="canonical"')) {
        $ValidArticles++
    }
}
Write-Host "✅ Conformité SEO & YMYL : $ValidArticles / $($PostHtmlFiles.Count) articles possèdent rel='sponsored nofollow', rel='canonical' et 'Not Legal Advice'." -ForegroundColor Green
