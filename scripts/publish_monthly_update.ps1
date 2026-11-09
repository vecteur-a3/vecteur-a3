# Chemin exact : scripts/publish_monthly_update.ps1
# Objectif : Exécuter l'audit mensuel YMYL, mettre à jour les fichiers JSON/Markdown,
#            créer le commit Git et pousser vers GitHub pour mettre à jour https://privacyanalyticsintel.com/
#
# Utilisation le 1er de chaque mois :
#   pwsh -File scripts/publish_monthly_update.ps1 -ForceAll

param (
    [switch]$ForceAll
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path "hugo.toml")) {
    Write-Error "ERREUR : Exécutez ce script depuis C:\Users\RDPUser\Documents\vecteur-a3"
    exit 1
}

$TodayIso = (Get-Date).ToString("yyyy-MM-dd")

# 1. Vérifier que le terminal est bien connecté à GitHub
Write-Host "`n=== 1. VÉRIFICATION DE LA CONNEXION GITHUB ===" -ForegroundColor Cyan
gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Session GitHub expirée. Reconnexion..." -ForegroundColor Yellow
    gh auth login --hostname github.com --git-protocol https --web -s workflow
}
gh auth setup-git

# 2. Exécuter le script de mise à jour des dates last_verified (si demandé avec -ForceAll ou si >= 60 jours)
Write-Host "`n=== 2. EXÉCUTION DE LA MISE À JOUR DES DONNÉES (last_verified) ===" -ForegroundColor Cyan
if ($ForceAll) {
    pwsh -NoProfile -ExecutionPolicy Bypass -File "scripts/update_monthly_freshness.ps1" -ForceAll
} else {
    pwsh -NoProfile -ExecutionPolicy Bypass -File "scripts/update_monthly_freshness.ps1"
}

# 3. Sécurité : s'assurer qu'aucun dossier temporaire (public, backups, .cache) n'est indexé
git rm -r --cached public resources .cache backups 2>$null | Out-Null

# 4. Indexer tous les fichiers mis à jour (JSON, articles Markdown, scripts)
Write-Host "`n=== 3. PRÉPARATION DU COMMIT GIT ===" -ForegroundColor Cyan
git add -A

$PendingChanges = git status --porcelain
if ($PendingChanges) {
    Write-Host "Fichiers modifiés prêts à être envoyés :" -ForegroundColor Yellow
    git status --short
    git commit -m "chore(data): monthly YMYL freshness audit and last_verified update ($TodayIso)"
    Write-Host "[OK] Commit créé avec succès." -ForegroundColor Green
} else {
    Write-Host "[INFO] Aucun nouveau changement local à committer (déjà enregistré dans le commit local)." -ForegroundColor Gray
}

# 5. Synchroniser avec le dépôt GitHub distant (évite l'erreur 'rejected - fetch first') et pousser
Write-Host "`n=== 4. SYNCHRONISATION ET ENVOI VERS GITHUB (git push) ===" -ForegroundColor Cyan
git fetch origin main
git merge origin/main -X ours --no-edit -m "chore(git): merge remote main before monthly update push"
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n================================================================================" -ForegroundColor Green
    Write-Host "✅ MISE À JOUR MENSUELLE ENVOYÉE SUR GITHUB AVEC SUCCÈS !" -ForegroundColor Green
    Write-Host "-> GitHub Actions compile et déploie actuellement votre site (environ 30 secondes)." -ForegroundColor Cyan
    Write-Host "-> Suivez le déploiement ici : https://github.com/vecteur-a3/vecteur-a3/actions" -ForegroundColor Cyan
    Write-Host "-> Site en ligne mis à jour  : https://privacyanalyticsintel.com/" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Green
} else {
    Write-Error "Échec lors du git push origin main. Vérifiez le message ci-dessus."
    exit 1
}
