<!-- Chemin exact : docs/A_VERIFIER.md -->
# Liste de Vérification Manuelle Avant Mise en Production — Projet Vecteur A3

Ce document centralise l'ensemble des vérifications manuelles à effectuer par l'administrateur avant l'ouverture commerciale publique du site **Vecteur A3**. Tant qu'un point relatif aux données d'un outil ou d'un framework n'est pas vérifié manuellement, le champ correspondant reste à `null` avec `"_a_verifier": true` dans `data/tools.json` ou `data/frameworks.json`.

---

## Priorité 1 — Pipeline RSS, Licences de Réutilisation & Suivi Poli de l'EDPS

1. **Conformité Licence CNIL (`CC-BY-ND 4.0 FR`) — Déjà actif, à maintenir :**
   - Page officielle : <https://www.cnil.fr/fr/mentions-legales>
   - Licence : <https://creativecommons.org/licenses/by-nd/4.0/deed.fr>
   - **Règle stricte :** Conserver `"allow_truncation": False` sur le flux `cnil-en` (`https://www.cnil.fr/en/rss.xml`) dans `scripts/ingest_privacy.py`. Ne jamais tronquer ni modifier le résumé ou le titre ; afficher uniquement le titre exact, le lien officiel, la date d'extraction (`JJ/MM/AAAA`), le lien de licence et la mention `Source : CNIL – https://www.cnil.fr`.
2. **Option éditoriale sur l'extrait EDPB (`INCLUDE_EDPB_CLEANED_EXCERPT`) :**
   - Page officielle : <https://www.edpb.europa.eu/copyright_en>
   - Flux actifs : <https://www.edpb.europa.eu/feed/news_en> et <https://www.edpb.europa.eu/feed/publications_en>
   - **État actuel :** `INCLUDE_EDPB_CLEANED_EXCERPT = False` par défaut dans `scripts/ingest_privacy.py` (affiche titre exact + date + lien officiel + attribution, sans troncature). Si vous décidez d'afficher un extrait nettoyé de 160 caractères uniquement sur `edpb-news`, passez cette constante à `True` après avoir validé que la troncature ne dénature pas le sens des brèves.
3. **Revérification périodique et polie du flux de l'EDPS (`HTTP 403 Forbidden`) :**
   - Flux concerné : <https://www.edps.europa.eu/feed/news_en> (lié depuis <https://www.edps.europa.eu/_en>)
   - **Constat du test runner du `2026-10-28` :** Bloqué en `HTTP 403 Forbidden` par le pare-feu (WAF) de `edps.europa.eu` sur les adresses IP des runners GitHub Actions, donc exclu de `OFFICIAL_DPA_FEEDS`.
   - **Action périodique (tous les 3 à 6 mois) :** Tester une seule requête en lecture seule avec le même `User-Agent` poli et transparent (`VecteurA3-PrivacyComplianceIntel/1.0`) pour vérifier si la politique de filtrage IP de l'EDPS a évolué. **Ne jamais tenter de contourner le blocage** (aucun proxy, aucune usurpation de User-Agent navigateur).

---

## Priorité 2 — Vérifications Tarifaires, TVA et Rétention dans `data/tools.json`

1. **Vérifier le statut HT/TTC (TVA) au checkout de Simple Analytics, Fathom Analytics et Piwik PRO :**
   - **Simple Analytics** ($20/mois pour 100k pages vues) : vérifier l'affichage de la TVA à l'étape de paiement sur <https://www.simpleanalytics.com/pricing>. Renseigner ensuite `"starting_price"` dans `data/tools.json`.
   - **Fathom Analytics** ($15/mois jusqu'à 100k pages vues) : vérifier l'affichage de la TVA au checkout sur <https://usefathom.com/pricing>.
   - **Piwik PRO Analytics Suite** (€36/mois sur le plan Business) : vérifier l'affichage HT/TTC sur <https://piwik.pro/business-plan/> et <https://piwik.pro/pricing/>.
2. **Trancher l'écart d'affichage USD vs EUR sur Matomo Cloud (`matomo-analytics`) :**
   - Page officielle : <https://matomo.org/pricing/> (et <https://fr.matomo.org/pricing/>)
   - **Point à vérifier :** Confirmer le montant que vous souhaitez retenir entre **USD 26/month excl. tax** (affiché dans le corps de page) et **EUR 29/month excl. tax** (affiché dans la grille 50 000 hits/mois), puis renseigner `"starting_price"` et passer `"_a_verifier"` à `false`.
3. **Confirmer la formulation de rétention de Fathom Analytics (`fathom-analytics`) :**
   - Page officielle : <https://usefathom.com/data>
   - **Point à vérifier :** La documentation indique que le sel quotidien (*daily salt*) tourne à minuit UTC mais que les signatures SHA-256 des événements passés restent stockées en base sans durée maximale de purge explicite sur `/data`. Valider la formulation finale souhaitée dans `"data_retention"` avant de retirer `"_a_verifier": true`.
4. **Confirmer l'inscription du tarif sur devis de Google Analytics 360 (`google-analytics-4`) :**
   - Page officielle : <https://support.google.com/analytics/answer/10000067>
   - **Point à vérifier :** Si vous souhaitez publier une chaîne fixe dans `"starting_price"` (ex. `"Free tier (GA4 Standard, $0) / Custom enterprise contract quote for Google Analytics 360"`), remplacez `null` par cette valeur et retirez `"_a_verifier": true`.

---

## Priorité 3 — Détails Complémentaires (`data/tools.json` & `data/frameworks.json`)

1. **Plafond d'années de rétention des plans payants Simple Analytics :**
   - Page officielle : cliquer sur *Compare all features* sur <https://www.simpleanalytics.com/pricing> pour vérifier le plafond exact d'années de rétention par palier payant (au-delà des 30 jours du plan Free), puis compléter si souhaité `"data_retention"` sur `simple-analytics`.
2. **Directive CSP et intégration Shopify Web Pixels (`shopify-storefront`) :**
   - Pages officielles : <https://shopify.dev/docs/api/web-pixels-api>, <https://docs.simpleanalytics.com/install-on-other-platforms>, <https://plausible.io/docs/shopify-integration>, <https://usefathom.com/docs/integrations/shopify>.
   - **Point à vérifier :** Tant que `"csp_directive"` est à `null` (`"_a_verifier": true`), la page `cookieless-analytics-implementation-shopify-storefront` est automatiquement placée en `noindex` par la Quality Gate. Renseignez `"csp_directive"` et retirez `"_a_verifier": true` une fois votre arbitrage documentaire effectué pour faire passer la page en `index`.

---

## Priorité 4 — Identité de Production, Affiliation & Relecture Juridique

1. **Nom de domaine, e-mail de contact et outil d'analytics du site :**
   - Remplacer `ton-domaine-privacy-a3.com` et `contact@privacyanalyticsintel.com` dans `hugo.toml` et `static/CNAME`.
   - Remplacer `contact@privacyanalyticsintel.com` dans `content/legal/methodology.md` et `content/legal/privacy.md`.
2. **Identifiants et conditions des programmes d'affiliation (`scripts/generate_pages.py`) :**
   - Vérifier les conditions officielles (taux de commission, durée de cookie/attribution, interdiction d'enchérir sur les mots-clés de marque) et remplacer `A_REMPLACER_ID_AFFILIE` dans le dictionnaire `AFFILIATE_CONFIG` de `scripts/generate_pages.py`.
3. **Relecture juridique professionnelle (YMYL) :**
   - Faire relire `content/legal/privacy.md`, `content/legal/methodology.md` et `content/legal/disclaimer.md` par un avocat ou juriste spécialisé IP/IT avant l'ouverture commerciale.
