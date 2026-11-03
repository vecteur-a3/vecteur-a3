# Chemin exact : scripts/ingest_privacy.py
import inspect
import json
import logging
import os
import re
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Importation sécurisée de requests-cache (dégradation gracieuse si absent)
try:
    import requests_cache
    HAS_REQUESTS_CACHE = True
except ImportError:
    HAS_REQUESTS_CACHE = False

# Configuration du journal d'exécution (logging en français)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins absolus à partir de la racine du dépôt Vecteur A3
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TOOLS_FILE = os.path.join(DATA_DIR, 'tools.json')
FRAMEWORKS_FILE = os.path.join(DATA_DIR, 'frameworks.json')
OUTPUT_FILE = os.path.join(DATA_DIR, 'privacy_intel.json')

# Dossier et fichier dédiés au cache HTTP SQLite (restauré par actions/cache dans GitHub Actions)
CACHE_DIR = os.path.join(BASE_DIR, '.cache')
CACHE_DB_PATH = os.path.join(CACHE_DIR, 'http_cache.sqlite')
CACHE_EXPIRE_SECONDS = 3600  # Validité du cache HTTP : 1 heure (3600 secondes)

# Paramètres métier et réseau (Zéro scraping HTML, 1 requête par flux, pause de courtoisie)
MAX_EXCERPT_CHARS = 160
MAX_ITEMS_PER_FEED = 5
REQUEST_TIMEOUT = (5, 15)  # (5s connexion, 15s lecture)
FEED_COURTESY_DELAY_SECONDS = 2  # Pause entre deux flux RSS distincts
USER_AGENT = "VecteurA3-PrivacyComplianceIntel/1.0 (+https://github.com/vecteur-a3; Public RSS Reader)"

# OPTION ÉDITORIALE EDPB (Étape 0.e) :
# La licence de l'EDPB autorise la réutilisation avec mention de la source à condition de ne pas
# dénaturer le sens original. Par défaut (False), on n'affiche que le titre exact, la date,
# le lien officiel et l'attribution (summary_short reste "").
# Passez explicitement cette constante à True uniquement si vous décidez d'activer l'extrait nettoyé
# pour edpb-news (edpb-publications ayant de toute façon une balise <description> vide).
INCLUDE_EDPB_CLEANED_EXCERPT = False

# Liste stricte des 3 flux RSS officiels validés en HTTP 200 depuis le runner GitHub Actions le 2026-10-28.
# Les autorités exclues (EDPS en HTTP 403, ICO hors service en HTML, DPC sans flux XML)
# sont documentées dans docs/feeds_status.md.
OFFICIAL_DPA_FEEDS = [
    {
        "authority_id": "edpb-news",
        "authority_name": "European Data Protection Board (EDPB - News)",
        "short_authority": "European Data Protection Board (EDPB)",
        "jurisdiction": "European Union (EEA)",
        "rss_url": "https://www.edpb.europa.eu/feed/news_en",
        "official_portal": "https://www.edpb.europa.eu/news_en",
        "language": "en",
        "license": "EDPB Legal Notice (Commercial & non-commercial reuse authorized with source acknowledgement)",
        "license_url": "https://www.edpb.europa.eu/copyright_en",
        "attribution_template": (
            "Source: European Data Protection Board (EDPB) - https://www.edpb.europa.eu "
            "(Extracted on {extraction_date_ddmmyyyy}, EDPB Legal Notice: https://www.edpb.europa.eu/copyright_en)"
        ),
        "display_policy": "cleaned_excerpt_optional" if INCLUDE_EDPB_CLEANED_EXCERPT else "title_link_attribution_only",
        "allow_truncation": bool(INCLUDE_EDPB_CLEANED_EXCERPT),
        "test_status": "VERIFIED_HTTP_200_XML_RUNNER",
        "last_verified_feed": "2026-10-28"
    },
    {
        "authority_id": "edpb-publications",
        "authority_name": "European Data Protection Board (EDPB - Guidelines & Publications)",
        "short_authority": "European Data Protection Board (EDPB)",
        "jurisdiction": "European Union (EEA)",
        "rss_url": "https://www.edpb.europa.eu/feed/publications_en",
        "official_portal": "https://www.edpb.europa.eu/news_en",
        "language": "en",
        "license": "EDPB Legal Notice (Commercial & non-commercial reuse authorized with source acknowledgement)",
        "license_url": "https://www.edpb.europa.eu/copyright_en",
        "attribution_template": (
            "Source: European Data Protection Board (EDPB) - https://www.edpb.europa.eu "
            "(Extracted on {extraction_date_ddmmyyyy}, EDPB Legal Notice: https://www.edpb.europa.eu/copyright_en)"
        ),
        "display_policy": "title_link_attribution_only",
        "allow_truncation": False,  # Balise <description> vide sur ce flux : jamais remplacée par le titre
        "test_status": "VERIFIED_HTTP_200_XML_RUNNER",
        "last_verified_feed": "2026-10-28"
    },
    {
        "authority_id": "cnil-en",
        "authority_name": "CNIL (French Data Protection Authority - English Feed)",
        "short_authority": "CNIL",
        "jurisdiction": "France / European Union",
        "rss_url": "https://www.cnil.fr/en/rss.xml",
        "official_portal": "https://www.cnil.fr/fr/mentions-legales",
        "language": "en",
        "license": "CC-BY-ND 4.0 FR (NoDerivatives - Pas de modifications)",
        "license_url": "https://creativecommons.org/licenses/by-nd/4.0/deed.fr",
        "attribution_template": (
            "Source : CNIL – https://www.cnil.fr "
            "(Extrait le {extraction_date_ddmmyyyy}, licence CC-BY-ND 4.0 FR : https://creativecommons.org/licenses/by-nd/4.0/deed.fr)"
        ),
        "display_policy": "strict_no_derivatives_title_only",
        "allow_truncation": False,  # Licence CC-BY-ND 4.0 FR : interdiction stricte de modifier/tronquer le texte
        "test_status": "VERIFIED_HTTP_200_XML_RUNNER",
        "last_verified_feed": "2026-10-28"
    }
]


class LoggedRetry(Retry):
    """
    Sous-classe de urllib3.util.Retry qui journalise explicitement en français
    chaque tentative de répétition (retry) sur erreur transitoire (408, 429, 5xx).
    Note : HTTP 403 est exclu de status_forcelist pour ne jamais forcer un pare-feu (WAF).
    """
    def increment(self, method=None, url=None, response=None, error=None, _pool=None, _stacktrace=None):
        new_retry = super().increment(
            method=method, url=url, response=response, error=error, _pool=_pool, _stacktrace=_stacktrace
        )
        attempt_num = 5 - (new_retry.total if isinstance(new_retry.total, int) else 0)
        if response is not None:
            retry_after = response.headers.get("Retry-After", "non spécifié")
            logger.warning(
                f"[RETRY #{attempt_num}] Statut HTTP {response.status} reçu sur {url} "
                f"(En-tête Retry-After: {retry_after}). Attente backoff + jitter en cours..."
            )
        elif error is not None:
            logger.warning(
                f"[RETRY #{attempt_num}] Erreur réseau transitoire sur {url} ({error}). "
                f"Attente backoff + jitter en cours..."
            )
        return new_retry


def clean_plain_excerpt(raw_text, max_chars=MAX_EXCERPT_CHARS):
    """
    Nettoie un extrait HTML/texte uniquement lorsque la licence du flux l'autorise
    et que l'option éditoriale est activée. Si raw_text est vide, retourne "".
    """
    if not raw_text:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(raw_text))
    for ch, repl in [("|", "-"), ("[", "("), ("]", ")"), ("`", "'"), ("<", ""), (">", ""), ("#", ""), ("*", "")]:
        text = text.replace(ch, repl)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    if len(text) > max_chars:
        return text[:max_chars - 3].rstrip() + "..."
    return text


def normalize_exact_title(raw_title):
    """
    Normalise uniquement les espaces/retours à la ligne d'un titre XML officiel
    SANS jamais le tronquer ni modifier ses mots (conformité CC-BY-ND 4.0 FR et EDPB).
    """
    if not raw_title:
        return ""
    return re.sub(r"\s+", " ", str(raw_title)).strip()


def init_sqlite_wal_mode(db_path):
    """
    Active le mode WAL (Write-Ahead Logging) et un timeout de 30s sur SQLite
    pour prévenir l'erreur 'OperationalError: database is locked'.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    try:
        with sqlite3.connect(db_path, timeout=30.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
    except sqlite3.Error as e:
        logger.warning(f"Impossible d'activer le mode WAL sur SQLite ({db_path}) : {e}")


def create_resilient_session():
    """
    Crée une session HTTP résiliente combinant cache SQLite persistant et
    politique de répétition conforme RFC 9110 (403 exclu, 429 avec Retry-After, 408/5xx avec jitter).
    """
    if HAS_REQUESTS_CACHE:
        init_sqlite_wal_mode(CACHE_DB_PATH)
        try:
            backend = requests_cache.SQLiteCache(
                db_path=CACHE_DB_PATH,
                wal=True,
                timeout=30.0
            )
            session = requests_cache.CachedSession(
                backend=backend,
                expire_after=CACHE_EXPIRE_SECONDS,
                allowable_methods=('GET', 'HEAD'),
                allowable_codes=(200,),
                ignored_parameters=['api_key', 'token', 'access_token', 'auth', 'key'],
                stale_if_error=True  # Autorise l'usage d'une réponse réelle en cache SQLite en cas de panne réseau
            )
            logger.info(f"Cache HTTP SQLite activé ({CACHE_DB_PATH}, expiration: {CACHE_EXPIRE_SECONDS}s).")
        except Exception as e:
            logger.warning(f"Échec d'initialisation du cache SQLite ({e}). Repli sur requests.Session standard.")
            session = requests.Session()
    else:
        logger.warning("Bibliothèque requests-cache absente. Exécution sans cache HTTP SQLite.")
        session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5"
    })

    retry_kwargs = {
        "total": 4,
        "connect": 3,
        "read": 3,
        "status_forcelist": [408, 429, 500, 502, 503, 504],
        "allowed_methods": frozenset(["HEAD", "GET", "OPTIONS"]),
        "backoff_factor": 1.0,
        "respect_retry_after_header": True,
        "raise_on_status": False
    }

    supported_params = inspect.signature(Retry.__init__).parameters
    if "backoff_jitter" in supported_params:
        retry_kwargs["backoff_jitter"] = 1.0
    if "backoff_max" in supported_params:
        retry_kwargs["backoff_max"] = 60.0

    retry_strategy = LoggedRetry(**retry_kwargs)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def safe_get_xml_feed(session, url, source_name):
    """
    Exécute une requête GET unique avec User-Agent explicite, vérifie le code HTTP
    et contrôle que l'en-tête Content-Type n'est pas une page HTML avant le parsing XML.
    """
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        from_cache = getattr(response, "from_cache", False)

        if response.status_code == 403:
            logger.warning(
                f"[{source_name}] Accès refusé (HTTP 403 Forbidden) sur {url}. "
                f"Aucune relance effectuée (respect strict du WAF distant)."
            )
            return None

        if response.status_code == 429:
            logger.warning(
                f"[{source_name}] Quota dépassé (HTTP 429 Too Many Requests) persistant sur {url}."
            )
            return None

        response.raise_for_status()

        content_type = (response.headers.get("Content-Type", "") or "").lower()
        if "html" in content_type and "xml" not in content_type:
            logger.warning(
                f"[{source_name}] Content-Type non-XML détecté ('{content_type}') sur {url}. "
                f"Flux ignoré (zéro scraping HTML)."
            )
            return None

        logger.info(
            f"[{source_name}] Réponse HTTP {response.status_code} | Content-Type: '{content_type}' "
            f"({'depuis le CACHE SQLite' if from_cache else 'via RÉSEAU direct'})."
        )
        return response

    except requests.exceptions.Timeout as e:
        logger.warning(f"[{source_name}] Délai d'attente dépassé (Timeout {REQUEST_TIMEOUT}s) sur {url} : {e}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"[{source_name}] Flux distant indisponible sur {url} : {e}")
    return None


def load_previous_real_feed_items(output_file_path):
    """
    Charge les dernières publications réelles déjà présentes dans data/privacy_intel.json
    pour servir de cache de secours par autorité si un flux distant est temporairement indisponible.
    Exclut formellement toute entrée marquée _exemple: True ou dépourvue de licence/attribution.
    """
    cached_by_authority = {}
    if not os.path.exists(output_file_path):
        return cached_by_authority

    try:
        with open(output_file_path, "r", encoding="utf-8") as f:
            prev_data = json.load(f)
        for item in prev_data.get("regulatory_updates", []):
            if item.get("_exemple", False):
                continue
            auth_id = item.get("authority_id")
            # On ne conserve que les entrées réelles dotées du nouveau schéma de licence vérifié
            if auth_id and item.get("license_url") and item.get("attribution_text"):
                cached_by_authority.setdefault(auth_id, []).append(item)
    except Exception as e:
        logger.warning(f"Impossible de lire le cache applicatif précédent ({output_file_path}) : {e}")

    return cached_by_authority


def parse_rss_or_atom_xml(xml_bytes, feed_meta):
    """
    Valide et analyse le XML d'un flux RSS 2.0 (<item>) ou Atom (<entry>) en respectant
    la licence propre à chaque autorité :
    - Titre exact non modifié ni tronqué.
    - Date d'extraction au format JJ/MM/AAAA injectée dans le modèle d'attribution.
    - Pour la CNIL (CC-BY-ND 4.0 FR) et par défaut pour l'EDPB : summary_short = "" (aucune troncature).
    - Si <description> est vide (ex: edpb-publications), summary_short reste "" (jamais remplacé par le titre).
    """
    root = ET.fromstring(xml_bytes)
    items = []

    now_utc = datetime.now(timezone.utc)
    today_iso = now_utc.strftime("%Y-%m-%d")
    today_ddmmyyyy = now_utc.strftime("%d/%m/%Y")

    allow_truncation = bool(feed_meta.get("allow_truncation", False))
    attribution_text = feed_meta["attribution_template"].format(
        extraction_date_ddmmyyyy=today_ddmmyyyy
    )

    rss_items = root.findall('./channel/item')
    for idx, elem in enumerate(rss_items[:MAX_ITEMS_PER_FEED]):
        exact_title = normalize_exact_title(elem.findtext('title', ''))
        if not exact_title:
            continue

        link = (elem.findtext('link', '') or feed_meta['official_portal']).strip()
        pub_raw = (elem.findtext('pubDate', '') or '').strip()
        desc_raw = (elem.findtext('description', '') or '').strip()

        dt_iso = ""
        if pub_raw:
            try:
                dt_iso = parsedate_to_datetime(pub_raw).astimezone(timezone.utc).isoformat()
            except Exception:
                dt_iso = pub_raw

        # Gestion stricte du résumé selon la politique de licence du flux :
        # - Jamais de remplacement par le titre si desc_raw est vide.
        # - Jamais de troncature si allow_truncation est False (CNIL CC-BY-ND 4.0 FR & défaut EDPB).
        if allow_truncation and desc_raw:
            summary_short = clean_plain_excerpt(desc_raw, MAX_EXCERPT_CHARS)
        else:
            summary_short = ""

        items.append({
            "id": f"dpa-{feed_meta['authority_id']}-{idx + 1}",
            "authority_id": feed_meta["authority_id"],
            "authority_name": feed_meta["authority_name"],
            "short_authority": feed_meta["short_authority"],
            "jurisdiction": feed_meta["jurisdiction"],
            "language": feed_meta["language"],
            "title": exact_title,
            "published_date": dt_iso,
            "summary_short": summary_short,
            "official_url": link if link.startswith(("https://", "http://")) else feed_meta["official_portal"],
            "license": feed_meta["license"],
            "license_url": feed_meta["license_url"],
            "attribution_text": attribution_text,
            "display_policy": feed_meta["display_policy"],
            "extraction_date_ddmmyyyy": today_ddmmyyyy,
            "feed_test_status": feed_meta["test_status"],
            "last_verified": today_iso
        })

    # Support Atom (<entry>) si le flux n'utilise pas <channel>/<item>
    if not items:
        atom_entries = root.findall('{http://www.w3.org/2005/Atom}entry') or root.findall('.//entry')
        for idx, entry in enumerate(atom_entries[:MAX_ITEMS_PER_FEED]):
            title_el = entry.find('{http://www.w3.org/2005/Atom}title') or entry.find('title')
            summary_el = entry.find('{http://www.w3.org/2005/Atom}summary') or entry.find('summary')
            updated_el = entry.find('{http://www.w3.org/2005/Atom}updated') or entry.find('updated')
            link_el = entry.find('{http://www.w3.org/2005/Atom}link') or entry.find('link')

            exact_title = normalize_exact_title(title_el.text if title_el is not None else '')
            if not exact_title:
                continue

            desc_raw = (summary_el.text or '').strip() if summary_el is not None else ''
            summary_short = clean_plain_excerpt(desc_raw, MAX_EXCERPT_CHARS) if (allow_truncation and desc_raw) else ""
            link_href = link_el.attrib.get('href', '').strip() if link_el is not None else feed_meta['official_portal']
            dt_iso = (updated_el.text.strip() if (updated_el is not None and updated_el.text) else "")

            items.append({
                "id": f"dpa-{feed_meta['authority_id']}-{idx + 1}",
                "authority_id": feed_meta["authority_id"],
                "authority_name": feed_meta["authority_name"],
                "short_authority": feed_meta["short_authority"],
                "jurisdiction": feed_meta["jurisdiction"],
                "language": feed_meta["language"],
                "title": exact_title,
                "published_date": dt_iso,
                "summary_short": summary_short,
                "official_url": link_href if link_href.startswith(("https://", "http://")) else feed_meta["official_portal"],
                "license": feed_meta["license"],
                "license_url": feed_meta["license_url"],
                "attribution_text": attribution_text,
                "display_policy": feed_meta["display_policy"],
                "extraction_date_ddmmyyyy": today_ddmmyyyy,
                "feed_test_status": feed_meta["test_status"],
                "last_verified": today_iso
            })

    return items


def fetch_dpa_regulatory_feeds(session, previous_real_cache):
    """
    Interroge séquentiellement les 3 flux RSS actifs avec pause de courtoisie.
    En cas d'échec d'un flux, réutilise uniquement la dernière donnée réelle en cache
    pour cette autorité (zéro donnée fictive inventée).
    """
    collected = []
    live_feeds_ok = 0

    for idx, feed_meta in enumerate(OFFICIAL_DPA_FEEDS):
        if idx > 0:
            time.sleep(FEED_COURTESY_DELAY_SECONDS)

        auth_id = feed_meta["authority_id"]
        label = feed_meta["authority_name"]
        url = feed_meta["rss_url"]

        logger.info(f"Interrogation du flux officiel ({idx + 1}/{len(OFFICIAL_DPA_FEEDS)}) : {label} -> {url}")
        resp = safe_get_xml_feed(session, url, label)

        if resp is not None:
            try:
                parsed_items = parse_rss_or_atom_xml(resp.content, feed_meta)
                if parsed_items:
                    collected.extend(parsed_items)
                    live_feeds_ok += 1
                    logger.info(
                        f"[{label}] {len(parsed_items)} publications validées "
                        f"(politique: {feed_meta['display_policy']}, licence: {feed_meta['license']})."
                    )
                    continue
                else:
                    logger.warning(f"[{label}] Aucun élément XML RSS/Atom trouvé dans le flux.")
            except ET.ParseError as e:
                logger.warning(f"[{label}] XML malformé ou invalide ({e}).")

        # Repli exclusivement sur les dernières données réelles déjà mises en cache pour cette autorité
        cached_items = previous_real_cache.get(auth_id, [])
        if cached_items:
            logger.warning(
                f"[{label}] Flux distant indisponible : conservation des {len(cached_items)} "
                f"dernières publications réelles en cache local."
            )
            collected.extend(cached_items)
        else:
            logger.warning(
                f"[{label}] Flux distant indisponible et aucune donnée réelle en cache : "
                f"flux ignoré (zéro donnée fictive injectée)."
            )

    return collected, live_feeds_ok


def load_and_validate_curated_tools(file_path):
    """
    Charge et valide strictement la matrice curée data/tools.json.
    Préserve les drapeaux _a_verifier et les champs null (starting_price, data_retention)
    pour que generate_pages.py applique les formulations prudentes.
    """
    if not os.path.exists(file_path):
        logger.critical(f"ÉCHEC CRITIQUE : Matrice curée introuvable ({file_path}). Arrêt immédiat (exit 1).")
        sys.exit(1)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
    except Exception as e:
        logger.critical(f"ÉCHEC CRITIQUE : Impossible de décoder {file_path} ({e}). Arrêt immédiat (exit 1).")
        sys.exit(1)

    tools = payload.get("tools", [])
    if len(tools) < 3:
        logger.critical("ÉCHEC CRITIQUE : data/tools.json doit contenir au moins 3 outils réels pour le Decoy Effect.")
        sys.exit(1)

    valid_tools = []
    # starting_price et data_retention peuvent être à null lorsque _a_verifier est true
    required_non_null_keys = [
        "id", "name", "role", "cookies_by_default",
        "ip_handling", "server_region", "source_url", "last_verified"
    ]

    for tool in tools:
        if tool.get("_exemple", False):
            logger.error(f"Outil '{tool.get('name', 'inconnu')}' ignoré : encore marqué _exemple: true.")
            continue
        missing = [k for k in required_non_null_keys if not tool.get(k)]
        if missing:
            logger.error(f"Outil '{tool.get('name', 'inconnu')}' ignoré : champs obligatoires manquants {missing}.")
            continue
        if not str(tool["source_url"]).startswith(("https://", "http://")):
            logger.error(f"Outil '{tool['name']}' ignoré : source_url invalide ({tool['source_url']}).")
            continue
        valid_tools.append(tool)

    if len(valid_tools) < 3:
        logger.critical("ÉCHEC CRITIQUE : Moins de 3 outils valides après contrôle YMYL des sources officielles.")
        sys.exit(1)

    ambiguous_count = sum(1 for t in valid_tools if t.get("_a_verifier", False))
    logger.info(
        f"[Matrice Tools] {len(valid_tools)} outils techniques validés depuis {file_path} "
        f"(dont {ambiguous_count} avec champs partiels marqués _a_verifier: true)."
    )
    return valid_tools, payload.get("metadata", {}).get("freshness_threshold_days", 90)


def load_and_validate_frameworks(file_path):
    """Charge et valide la matrice des frameworks web (data/frameworks.json)."""
    if not os.path.exists(file_path):
        logger.warning(f"Fichier {file_path} absent. Les guides frameworks ne seront pas générés.")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        frameworks = [fw for fw in payload.get("frameworks", []) if not fw.get("_exemple", False)]
        logger.info(f"[Matrice Frameworks] {len(frameworks)} profils de frameworks chargés depuis {file_path}.")
        return frameworks
    except Exception as e:
        logger.error(f"Erreur de lecture sur {file_path} ({e}).")
        return []


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. Validation critique de la matrice curée data/tools.json
    valid_tools, freshness_days = load_and_validate_curated_tools(TOOLS_FILE)

    # 2. Chargement de la matrice des 6 frameworks (data/frameworks.json)
    frameworks = load_and_validate_frameworks(FRAMEWORKS_FILE)

    # 3. Lecture du cache applicatif précédent (uniquement les publications réelles vérifiées)
    previous_real_cache = load_previous_real_feed_items(OUTPUT_FILE)

    # 4. Collecte résiliente des 3 flux RSS officiels (edpb-news, edpb-publications, cnil-en)
    session = create_resilient_session()
    regulatory_items, live_feeds_ok = fetch_dpa_regulatory_feeds(session, previous_real_cache)

    # 5. Écriture du fichier consolidé data/privacy_intel.json
    output_payload = {
        "_comment": "Généré automatiquement par scripts/ingest_privacy.py pour Vecteur A3",
        "metadata": {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "freshness_threshold_days": freshness_days,
            "validated_tools_count": len(valid_tools),
            "frameworks_count": len(frameworks),
            "regulatory_items_count": len(regulatory_items),
            "live_dpa_feeds_ok": f"{live_feeds_ok}/{len(OFFICIAL_DPA_FEEDS)}",
            "edpb_cleaned_excerpt_enabled": INCLUDE_EDPB_CLEANED_EXCERPT,
            "feeds_status_doc": "docs/feeds_status.md"
        },
        "dpa_feeds_registry": OFFICIAL_DPA_FEEDS,
        "tools": valid_tools,
        "frameworks": frameworks,
        "regulatory_updates": regulatory_items
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)

    logger.info(
        f"Pipeline d'ingestion A3 terminé : {len(valid_tools)} outils, "
        f"{len(frameworks)} frameworks et {len(regulatory_items)} publications officielles "
        f"({live_feeds_ok}/{len(OFFICIAL_DPA_FEEDS)} flux RSS directs OK) sauvegardés dans {OUTPUT_FILE}."
    )


if __name__ == "__main__":
    main()
