# Chemin exact : scripts/generate_pages.py
import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone

# Nécessite : pip install python-frontmatter
import frontmatter

# Configuration du journal d'exécution (logging en français)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemins absolus sécurisés depuis la racine du projet Vecteur A3
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "privacy_intel.json")
POSTS_DIR = os.path.join(BASE_DIR, "content", "posts")
STATIC_IMAGES_DIR = os.path.join(BASE_DIR, "static", "images")
DEFAULT_COVER_REL_PATH = "/images/default-cover.svg"

# Publication progressive (Drip Publishing) paramétrable : 5 pages par défaut
DEFAULT_MAX_PAGES_PER_RUN = 5
DEFAULT_FRESHNESS_THRESHOLD_DAYS = 90

# Contraintes de longueur de la Quality Gate
AIDA_BRIEF_MIN_WORDS = 55
AIDA_BRIEF_MAX_WORDS = 175
ARTICLE_MIN_TOTAL_WORDS = 240

# Expressions juridiques absolues formellement INTERDITES (Règle YMYL Priorité Maximale)
FORBIDDEN_YMYL_PHRASES = [
    r"\bis gdpr compliant\b",
    r"\bguarantees compliance\b",
    r"\bno cookie banner needed\b",
    r"\blegal in germany\b",
    r"\b100%\s+gdpr\s+compliant\b",
    r"\bcertified\s+gdpr\s+compliant\b"
]

# Bandeau d'avertissement obligatoire sur chaque page générée
MANDATORY_DISCLAIMER_TEXT = (
    "**Not Legal Advice:** This technical audit compares software specifications documented by each vendor "
    "and does not constitute legal advice or a formal regulatory compliance opinion."
)

# Libellés courts pour le fil d'Ariane (div.report-breadcrumb) et le KPI Audit Focus des frameworks
FRAMEWORK_SHORT_KEYWORDS = {
    "nextjs-ecommerce": "Next.js App Router",
    "react-spa": "React 19 SPA & SSR",
    "astro-static": "Astro Static & Islands",
    "vue-spa": "Vue 3 & Nuxt SSR",
    "remix-ssr": "Remix Full-Stack SSR",
    "shopify-storefront": "Shopify Web Pixels"
}

# Dictionnaire des partenaires d'affiliation A3
AFFILIATE_CONFIG = {
    "simple-analytics": {
        "nom": "Simple Analytics",
        "url": "https://www.simpleanalytics.com/",
        "proposition": "Evaluate an EU-hosted, cookieless web analytics layer according to vendor technical documentation.",
        "btn_texte": "Explore Simple Analytics & Docs",
        "spec_badge_1": "Cookieless by Default (Vendor Docs)",
        "spec_badge_2": "EU Server Hosting (Netherlands)",
        "spec_badge_3": "No Raw IP Storage"
    },
    "fathom-analytics": {
        "nom": "Fathom Analytics",
        "url": "https://usefathom.com/",
        "proposition": "Deploy a cookieless analytics script with EU Data Isolation proxy routing (Germany/Finland) prior to US storage per vendor docs.",
        "btn_texte": "Explore Fathom Technical Specs",
        "spec_badge_1": "Cookieless Architecture",
        "spec_badge_2": "EU Isolation Routing (DE/FI Proxy)",
        "spec_badge_3": "Built-in Uptime & Event Logs"
    },
    "plausible-analytics": {
        "nom": "Plausible Analytics",
        "url": "https://plausible.io/",
        "proposition": "Inspect an open-source, lightweight (< 1 KB) web analytics platform hosted in the European Union.",
        "btn_texte": "View Plausible Architecture",
        "spec_badge_1": "Open-Source (AGPLv3)",
        "spec_badge_2": "EU Hosted (Germany / Finland)",
        "spec_badge_3": "Daily Rotating Hash (No Cookies)"
    },
    "piwik-pro": {
        "nom": "Piwik PRO Analytics Suite",
        "url": "https://piwik.pro/",
        "proposition": "Enterprise analytics suite with integrated Consent Management Platform (CMP) and dedicated cloud options.",
        "btn_texte": "View Piwik PRO Specs",
        "spec_badge_1": "Integrated Enterprise CMP",
        "spec_badge_2": "EU / Dedicated Cloud",
        "spec_badge_3": "Configurable IP Masking"
    },
    "matomo-analytics": {
        "nom": "Matomo Analytics",
        "url": "https://matomo.org/",
        "proposition": "Full-featured open-source analytics with on-premise MySQL self-hosting and configurable IP masking.",
        "btn_texte": "View Matomo Specs",
        "spec_badge_1": "On-Premise Self-Hosting",
        "spec_badge_2": "Configurable Cookie Mode",
        "spec_badge_3": "Full Raw Log Ownership"
    }
}

# Visuel SVG vectoriel "Deep Teal Privacy Architecture" (800x450)
DEFAULT_COVER_SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" width="800" height="450">
  <defs>
    <linearGradient id="bgA3" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16"/>
      <stop offset="100%" stop-color="#115e59"/>
    </linearGradient>
    <linearGradient id="tealGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#14b8a6" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#0d9488" stop-opacity="0.0"/>
    </linearGradient>
  </defs>
  <rect width="800" height="450" fill="url(#bgA3)"/>
  <g stroke="#334155" stroke-width="1" stroke-dasharray="4 4" opacity="0.55">
    <line x1="60" y1="95" x2="740" y2="95"/>
    <line x1="60" y1="185" x2="740" y2="185"/>
    <line x1="60" y1="275" x2="740" y2="275"/>
    <line x1="60" y1="365" x2="740" y2="365"/>
    <line x1="230" y1="60" x2="230" y2="390"/>
    <line x1="400" y1="60" x2="400" y2="390"/>
    <line x1="570" y1="60" x2="570" y2="390"/>
  </g>
  <polygon points="60,365 60,270 190,240 310,190 430,210 560,145 740,120 740,365" fill="url(#tealGrad)"/>
  <polyline fill="none" stroke="#2dd4bf" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" points="60,270 190,240 310,190 430,210 560,145 740,120"/>
  <circle cx="190" cy="240" r="7" fill="#0d9488" stroke="#ffffff" stroke-width="2"/>
  <circle cx="310" cy="190" r="7" fill="#0d9488" stroke="#ffffff" stroke-width="2"/>
  <circle cx="560" cy="145" r="7" fill="#14b8a6" stroke="#ffffff" stroke-width="2"/>
  <circle cx="740" cy="120" r="8" fill="#10b981" stroke="#ffffff" stroke-width="2"/>
  <rect x="60" y="34" width="265" height="32" rx="16" fill="#134e4a" stroke="#2dd4bf" stroke-width="1"/>
  <circle cx="80" cy="50" r="5" fill="#2dd4bf"/>
  <text x="96" y="55" fill="#ccfbf1" font-family="system-ui, -apple-system, sans-serif" font-size="12.5" font-weight="700" letter-spacing="1">PRIVACY ARCHITECTURE AUDIT</text>
</svg>
"""


def format_framework_spec_text(raw_text, max_chars=600):
    """
    Formate les spécifications techniques issues de notre matrice locale curée data/frameworks.json :
    - Groupe d'abord les paires <script ...></script> en un seul bloc de code inline.
    - Transforme les balises isolées (<Script>, <Scripts />, <ClientRouter />, <head>, <body>) en code inline.
    - Évite que 'react-dom@19.3' ne soit converti en lien mailto: par le parseur Markdown.
    - Conserve la phrase technique complète sans coupure artificielle à 260 caractères.
    """
    if not raw_text:
        return "See official framework documentation."
    text = str(raw_text).replace("react-dom@19.3", "react-dom (v19.3)")
    text = re.sub(r"(<script[^>]*>\s*</script>|<[A-Za-z/][^>]*>)", r"`\1`", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars - 3].rstrip("` ") + "..."
    return text

def sanitize_third_party_text(raw_text, max_chars=220):
    """Assainit un champ de spécification technique issu des matrices JSON."""
    if not raw_text:
        return "Technical specification documented by official source."
    text = re.sub(r"<[^>]+>", " ", str(raw_text))
    for ch, repl in [("|", "-"), ("[", "("), ("]", ")"), ("`", "'"), ("<", ""), (">", ""), ("#", ""), ("*", "")]:
        text = text.replace(ch, repl)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars - 3].rstrip() + "..."
    return text


def preserve_exact_official_title(raw_title):
    """
    Conformité Licence CC-BY-ND 4.0 FR (CNIL) et EDPB Legal Notice :
    Conserve le titre officiel EXACT sans jamais le tronquer ni altérer ses mots.
    """
    if not raw_title:
        return ""
    return re.sub(r"\s+", " ", str(raw_title)).strip()


def sanitize_external_url(raw_url):
    """Vérifie qu'une URL externe commence par http:// ou https:// et neutralise les parenthèses."""
    if not raw_url or not isinstance(raw_url, str):
        return ""
    url = raw_url.strip()
    if not (url.startswith("https://") or url.startswith("http://")):
        return ""
    return url.replace(")", "%29").replace("(", "%28").replace(" ", "%20")


def format_prudent_price(tool, for_table=True):
    """Formulation prudente lorsque starting_price est null (_a_verifier: true)."""
    raw_price = tool.get("starting_price")
    verif_date = tool.get("last_verified", "2026-11-09")
    if raw_price:
        return sanitize_third_party_text(raw_price, 140 if for_table else 260)

    if for_table:
        return f"See vendor pricing page (as of {verif_date}; tax/tier details vary)"

    notes = tool.get("_notes_a_verifier") or {}
    note_price = notes.get("starting_price", "")
    if note_price:
        clean_note = re.sub(r"\s*—?\s*\[À VÉRIFIER[^\]]*\]", "", note_price).strip()
        return f"See vendor pricing page ({ sanitize_third_party_text(clean_note, 260) })"
    return f"See vendor pricing page (pricing or VAT treatment not explicitly stated in primary docs as of {verif_date})"


def format_prudent_retention(tool):
    """Formulation prudente lorsque data_retention est null."""
    raw_ret = tool.get("data_retention")
    verif_date = tool.get("last_verified", "2026-11-09")
    if raw_ret:
        return sanitize_third_party_text(raw_ret, 240)

    notes = tool.get("_notes_a_verifier") or {}
    note_ret = notes.get("data_retention", "")
    if note_ret:
        clean_note = re.sub(r"\s*—?\s*\[À VÉRIFIER[^\]]*\]", "", note_ret).strip()
        return f"See vendor documentation ({ sanitize_third_party_text(clean_note, 240) })"
    return f"See vendor documentation (retention ceiling not explicitly specified in primary docs as of {verif_date})"


def format_prudent_csp(framework):
    """Formulation prudente lorsque csp_directive est null."""
    raw_csp = framework.get("csp_directive")
    if raw_csp:
        return sanitize_third_party_text(raw_csp, 600)

    notes = framework.get("_notes_a_verifier") or {}
    note_csp = notes.get("csp_directive", "")
    if note_csp:
        clean_note = re.sub(r"\s*—?\s*\[À VÉRIFIER[^\]]*\]", "", note_csp).strip()
        return f"See official documentation ({ sanitize_third_party_text(clean_note, 600) })"
    return "See official framework documentation (sandbox CSP domains require manual verification)"


def ensure_default_cover_exists():
    """Crée ou met à jour static/images/default-cover.svg."""
    os.makedirs(STATIC_IMAGES_DIR, exist_ok=True)
    default_svg_path = os.path.join(STATIC_IMAGES_DIR, "default-cover.svg")
    with open(default_svg_path, "w", encoding="utf-8") as f:
        f.write(DEFAULT_COVER_SVG_CONTENT)
    logger.info(f"Visuel vectoriel A3 vérifié : {default_svg_path}")


def resolve_topic_image(slug):
    """Cherche une image dédiée au sujet dans static/images/, sinon renvoie default-cover.svg."""
    if not os.path.exists(STATIC_IMAGES_DIR):
        return DEFAULT_COVER_REL_PATH

    valid_exts = (".webp", ".png", ".jpg", ".jpeg", ".svg")
    try:
        files_in_dir = os.listdir(STATIC_IMAGES_DIR)
    except OSError:
        return DEFAULT_COVER_REL_PATH

    for ext in valid_exts:
        exact_name = f"{slug}{ext}"
        for disk_file in files_in_dir:
            if disk_file.lower() == exact_name.lower():
                return f"/images/{disk_file}"

    return DEFAULT_COVER_REL_PATH


def load_privacy_data(file_path):
    """Charge et vérifie data/privacy_intel.json."""
    if not os.path.exists(file_path):
        logger.critical(f"Fichier introuvable : {file_path}. Exécutez d'abord scripts/ingest_privacy.py.")
        sys.exit(1)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if "tools" not in data or "metadata" not in data:
            logger.critical("Structure JSON invalide dans data/privacy_intel.json.")
            sys.exit(1)
        return data
    except Exception as e:
        logger.critical(f"Erreur de lecture JSON sur {file_path} : {e}")
        sys.exit(1)


def compute_verification_age_days(date_str):
    """Calcule l'ancienneté en jours d'une date last_verified (format YYYY-MM-DD)."""
    if not date_str:
        return 9999
    try:
        dt = datetime.strptime(str(date_str).strip()[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).days
        return max(0, age_days)
    except Exception:
        return 9999


def build_real_decoy_table(tool_target, tool_alt, tool_decoy):
    """Construit le tableau comparatif Markdown à 3 options RÉELLES et vérifiées."""
    rows = []
    header = (
        "| Software Solution | Cookies by Default (Vendor Claim) | IP Address Handling | Server Region | Starting Price (As of Verified Date) | Official Source & Verification |\n"
        "|---|---|---|---|---|---|\n"
    )

    for idx, t in enumerate([tool_target, tool_alt, tool_decoy]):
        t_id = t.get("id", "")
        t_name = sanitize_third_party_text(t.get("name", "Analytics Tool"), 45)
        aff_info = AFFILIATE_CONFIG.get(t_id)

        if idx == 0 and aff_info:
            aff_url = sanitize_external_url(aff_info["url"])
            name_cell = f"[**{t_name}**]({aff_url} \"sponsored\")"
        else:
            name_cell = f"**{t_name}**"

        cookies = sanitize_third_party_text(t.get("cookies_by_default", ""), 95)
        ip_mode = sanitize_third_party_text(t.get("ip_handling", ""), 110)
        region = sanitize_third_party_text(t.get("server_region", ""), 95)
        price = format_prudent_price(t, for_table=True)
        src_url = sanitize_external_url(t.get("source_url", ""))
        verif_date = sanitize_third_party_text(t.get("last_verified", "N/A"), 15)
        src_cell = f"[Vendor Docs]({src_url}) *(Verified {verif_date})*" if src_url else "Missing Source"

        rows.append(f"| {name_cell} | {cookies} | {ip_mode} | {region} | {price} | {src_cell} |")

    latest_verif = max(t.get("last_verified", "2026-11-09") for t in [tool_target, tool_alt, tool_decoy])
    pricing_footnote = (
        f"\n*Pricing & Tax Notice: Prices and plan parameters are reported as of **{latest_verif}**; "
        f"tax/VAT treatment may vary by jurisdiction at checkout. Where a starting price displays "
        f"\"See vendor pricing page\", VAT inclusion/exclusion or multi-currency equivalence was not "
        f"explicitly stated on the vendor's primary pricing page.*\n"
    )

    return header + "\n".join(rows) + "\n" + pricing_footnote


def build_sources_and_ambiguity_notes_md(tools_list, context_item=None, page_category=""):
    """Génère un bloc Markdown de traçabilité sous les comparatifs."""
    lines = [
        "### Primary Documentation Sources & Verification Notes",
        ""
    ]
    seen_ids = set()
    all_tools = list(tools_list)
    if isinstance(context_item, dict) and context_item.get("source_url"):
        all_tools.append(context_item)

    for t in all_tools:
        t_id = t.get("id", "")
        if not t_id or t_id in seen_ids:
            continue
        seen_ids.add(t_id)

        t_name = sanitize_third_party_text(t.get("name", "Tool"), 60)
        src_url = sanitize_external_url(t.get("source_url", ""))
        verif_d = sanitize_third_party_text(t.get("last_verified", "2026-11-09"), 15)
        retention_str = format_prudent_retention(t)
        price_str = format_prudent_price(t, for_table=False)

        lines.append(
            f"- **{t_name}** ([Official Documentation]({src_url}) — *last verified {verif_d}*): "
            f"**Data Retention:** {retention_str}. **Pricing Note:** {price_str}."
        )

    if page_category == "framework_guide" and isinstance(context_item, dict):
        fw_name = sanitize_third_party_text(context_item.get("name", "Framework"), 60)
        fw_url = sanitize_external_url(context_item.get("official_docs_url", ""))
        fw_verif = sanitize_third_party_text(context_item.get("last_verified", "2026-11-09"), 15)
        lines.append(
            f"- **{fw_name} Integration Reference** ([Official Framework Docs]({fw_url}) — *last verified {fw_verif}*)."
        )

    return "\n".join(lines) + "\n"


def build_page_blueprints(data):
    """Prépare la file des 4 types de pages A3 à partir de data/privacy_intel.json."""
    tools_by_id = {t["id"]: t for t in data.get("tools", [])}
    frameworks = data.get("frameworks", [])
    reg_updates = data.get("regulatory_updates", [])

    t_simple = tools_by_id.get("simple-analytics")
    t_plausible = tools_by_id.get("plausible-analytics")
    t_fathom = tools_by_id.get("fathom-analytics")
    t_piwik = tools_by_id.get("piwik-pro")
    t_matomo = tools_by_id.get("matomo-analytics")
    t_ga4 = tools_by_id.get("google-analytics-4")

    blueprints = []

    # --- TYPE 1 : ALTERNATIVES À GOOGLE ANALYTICS 4 ---
    if t_simple and t_plausible and t_piwik and t_ga4:
        blueprints.append({
            "slug": "cookieless-google-analytics-4-alternatives-technical-audit",
            "title": "Cookieless Google Analytics 4 (GA4) Alternatives: Technical Architecture Comparison",
            "description": "Technical specification comparison of cookieless web analytics alternatives to Google Analytics 4 (cookie storage, IP handling, and EU server routing).",
            "page_category": "alternatives",
            "keyword": "GA4 Cookieless Alternatives",
            "target_tool_id": "simple-analytics",
            "tools_used": [t_simple, t_plausible, t_piwik, t_ga4],
            "context_item": t_ga4
        })

    # --- TYPE 2 : COMPARATIFS TECHNIQUES X VS Y (AVEC DECOY RÉEL) ---
    if t_simple and t_plausible and t_piwik:
        blueprints.append({
            "slug": "simple-analytics-vs-plausible-analytics-technical-comparison",
            "title": "Simple Analytics vs Plausible Analytics: Technical & Hosting Specification Audit",
            "description": "Side-by-side engineering comparison of Simple Analytics, Plausible Analytics, and Piwik PRO based on official vendor documentation.",
            "page_category": "comparison",
            "keyword": "Simple Analytics vs Plausible",
            "target_tool_id": "simple-analytics",
            "tools_used": [t_simple, t_plausible, t_piwik],
            "context_item": t_plausible
        })

    if t_simple and t_fathom and t_matomo:
        blueprints.append({
            "slug": "simple-analytics-vs-fathom-analytics-architecture-comparison",
            "title": "Simple Analytics vs Fathom Analytics: Cookieless Telemetry & EU Routing Comparison",
            "description": "Technical evaluation of Simple Analytics, Fathom Analytics, and Matomo Analytics covering cookie behavior, IP processing, and hosting regions.",
            "page_category": "comparison",
            "keyword": "Simple Analytics vs Fathom",
            "target_tool_id": "simple-analytics",
            "tools_used": [t_simple, t_fathom, t_matomo],
            "context_item": t_fathom
        })

    # --- TYPE 3 : GUIDES D'IMPLÉMENTATION PAR FRAMEWORK ---
    for fw in frameworks:
        t_target = tools_by_id.get(fw.get("target_tool_id", "simple-analytics"), t_simple)
        t_alt = tools_by_id.get(fw.get("alt_tool_id", "plausible-analytics"), t_plausible)
        t_decoy = tools_by_id.get(fw.get("decoy_tool_id", "piwik-pro"), t_piwik)
        if t_target and t_alt and t_decoy:
            fw_id = re.sub(r"[^a-z0-9]+", "-", fw["id"].lower()).strip("-")
            short_kw = FRAMEWORK_SHORT_KEYWORDS.get(
                fw["id"],
                re.sub(r"\s*\([^)]*\)", "", fw["name"]).strip() + " Analytics"
            )
            blueprints.append({
                "slug": f"cookieless-analytics-implementation-{fw_id}",
                "title": f"Cookieless Web Analytics Implementation Guide for {fw['name']}",
                "description": f"Technical integration guide for deploying cookieless web analytics in {fw['name']} ({fw['use_case']}) with CSP headers and routing notes.",
                "page_category": "framework_guide",
                "keyword": short_kw,
                "target_tool_id": t_target["id"],
                "tools_used": [t_target, t_alt, t_decoy],
                "context_item": fw
            })

    # --- TYPE 4 : VEILLE RÉGLEMENTAIRE FACTUELLE (DPA RSS DIGEST - EDPB & CNIL) ---
    if reg_updates and t_simple and t_plausible and t_piwik:
        blueprints.append({
            "slug": "data-protection-authority-web-analytics-publications-digest",
            "title": "Data Protection Authority (DPA) Publications & Web Analytics Technical Digest",
            "description": "Factual digest of recent official publications from European data protection authorities (EDPB and CNIL) with direct institutional links and license attributions.",
            "page_category": "regulatory_watch",
            "keyword": "DPA Regulatory Digest",
            "target_tool_id": "simple-analytics",
            "tools_used": [t_simple, t_plausible, t_piwik],
            "context_item": reg_updates
        })

    return blueprints


def generate_aida_markdown_a3(blueprint, image_url):
    """Génère le contenu Markdown structuré selon la progression AIDA et les règles YMYL & Licences."""
    cat = blueprint["page_category"]
    tools = blueprint["tools_used"]
    t_target, t_alt, t_decoy = tools[0], tools[1], tools[2]
    ctx = blueprint["context_item"]

    decoy_table_md = build_real_decoy_table(t_target, t_alt, t_decoy)
    sources_notes_md = build_sources_and_ambiguity_notes_md(tools, ctx, cat)

    target_src = sanitize_external_url(t_target["source_url"])
    target_verif = sanitize_third_party_text(t_target["last_verified"], 15)
    alt_src = sanitize_external_url(t_alt["source_url"])
    alt_verif = sanitize_third_party_text(t_alt["last_verified"], 15)

    if cat == "framework_guide":
        fw_name = sanitize_third_party_text(ctx.get("name", "Modern Frontend Framework"), 60)
        fw_docs = sanitize_external_url(ctx.get("official_docs_url", ""))
        fw_verif = sanitize_third_party_text(ctx.get("last_verified", "2026-11-09"), 15)
        csp_formatted = format_prudent_csp(ctx)

        aida_lines = [
            f"**Architectural Context:** Engineering teams building {fw_name} applications frequently evaluate cookieless analytics scripts to minimize client-side bundle overhead and avoid persistent browser storage.",
            f"**Documented Behavior:** According to {t_target['name']} and {t_alt['name']} technical documentation (last verified on {target_verif}), pageviews can be recorded via lightweight JavaScript hooks without setting browser cookies by default.",
            f"**Integration Trade-offs:** Unlike full enterprise suites such as {t_decoy['name']} that bundle tag managers and consent modules, dedicated cookieless scripts focus on aggregate traffic metrics and explicit Content Security Policy (CSP) directives.",
            f"**Verification Step:** Review the {fw_name} script integration parameters and official vendor documentation links below, and consult your legal counsel to validate your specific deployment."
        ]
        middle_section = f"""## Technical Integration Parameters for {fw_name}

> {MANDATORY_DISCLAIMER_TEXT}

When integrating a web analytics script into **{fw_name}** (*{sanitize_third_party_text(ctx.get('use_case', ''), 90)}*), developers must account for client-side routing transitions and Content Security Policy (CSP) headers documented by the framework maintainer ([Official {fw_name} Documentation]({fw_docs}) — *last verified {fw_verif}*):

#### Script Injection & Lifecycle Hook [Official Framework Docs &rarr;]({fw_docs})
- **`[COMPONENT]`** *Script Loading Strategy* — {format_framework_spec_text(ctx.get('script_component', ''), 600)}
- **`[ROUTING]`** *SPA Pageview Tracking* — {format_framework_spec_text(ctx.get('routing_behavior', ''), 600)}
- **`[CSP HEADER]`** *Content Security Policy* — `{csp_formatted}`
"""

    elif cat == "regulatory_watch":
        reg_list = ctx if isinstance(ctx, list) else []
        aida_lines = [
            "**Institutional Monitoring:** European Data Protection Authorities — specifically the European Data Protection Board (EDPB) and the French CNIL — regularly publish official guidelines and decisions regarding data protection, anonymisation, and audience measurement.",
            "**Strict License & Attribution Compliance:** This digest syndicates exact, unmodified official titles, publication dates, and direct institutional URLs from verified public XML feeds in strict accordance with the CNIL CC-BY-ND 4.0 FR (NoDerivatives) license and the EDPB Legal Notice.",
            f"**Technical Alignment:** Software architects use these primary institutional publications alongside vendor technical documentation (such as {t_target['name']} and {t_alt['name']}, verified on {target_verif}) when preparing architecture dossiers for their Data Protection Officer (DPO).",
            "**Verification Step:** Follow the official institutional links below to read the complete, authoritative texts directly on the EDPB and CNIL portals."
        ]
        reg_lines = [
            f"> {MANDATORY_DISCLAIMER_TEXT}",
            ""
        ]
        for item in reg_list[:15]:
            auth_name = sanitize_third_party_text(item.get("authority_name", "Data Protection Authority"), 80)
            pub_date = sanitize_third_party_text((item.get("published_date", "") or "")[:10], 15) or item.get("last_verified", "2026-11-09")
            exact_title = preserve_exact_official_title(item.get("title", "Official Publication"))
            off_url = sanitize_external_url(item.get("official_url", ""))
            lic_name = sanitize_third_party_text(item.get("license", "Official Reuse License"), 90)
            lic_url = sanitize_external_url(item.get("license_url", ""))
            attr_text = preserve_exact_official_title(item.get("attribution_text", ""))
            extr_date = sanitize_third_party_text(item.get("extraction_date_ddmmyyyy", ""), 15)
            summary_short = (item.get("summary_short") or "").strip()
            allow_cnil = item.get("authority_id", "") == "cnil-en"

            link_md = f"[Official Institutional Publication &rarr;]({off_url})" if off_url else ""
            lic_md = f"[{lic_name}]({lic_url})" if lic_url else lic_name

            reg_lines.append(f"#### {pub_date} — {auth_name}: {exact_title} {link_md}")
            reg_lines.append(
                f"- **`[MANDATORY ATTRIBUTION]`** {attr_text} — **License:** {lic_md} *(Extracted on {extr_date})*"
            )
            if summary_short and not allow_cnil:
                reg_lines.append(
                    f"- **`[CLEANED EXCERPT]`** {sanitize_third_party_text(summary_short, 160)}"
                )
            reg_lines.append("")

        middle_section = "## Recent Data Protection Authority (DPA) Official Publications (EDPB & CNIL)\n\n" + "\n".join(reg_lines)

    else:
        focus_name = sanitize_third_party_text(ctx.get("name", t_alt["name"]), 55)
        focus_src = sanitize_external_url(ctx.get("source_url", alt_src))
        focus_verif = sanitize_third_party_text(ctx.get("last_verified", alt_verif), 15)
        aida_lines = [
            f"**Evaluation Context:** Organizations reviewing {focus_name} frequently audit how browser cookies, visitor IP addresses, and regional server routing are handled across competing web analytics architectures.",
            f"**Vendor Documentation Findings:** According to official vendor documentation (last verified on {target_verif}), {t_target['name']} and {t_alt['name']} claim to operate without setting browser cookies by default, whereas {t_decoy['name']} provides configurable enterprise consent and hosting modes.",
            f"**Architectural Trade-offs:** Selecting between lightweight cookieless telemetry and a full enterprise suite ({t_decoy['name']}) depends on whether your engineering team requires raw user-level logs, self-hosted infrastructure, or simplified aggregate metrics.",
            "**Verification Step:** Inspect the verified technical specification matrix, retention notes, and official documentation links below before consulting your legal or privacy team."
        ]
        middle_section = f"""## Documented Technical Architecture: {t_target['name']} vs {focus_name}

> {MANDATORY_DISCLAIMER_TEXT}

When comparing **{t_target['name']}** ([Official Documentation]({target_src}), *last verified {target_verif}*) with **{focus_name}** ([Official Documentation]({focus_src}), *last verified {focus_verif}*), software engineers examine verifiable technical criteria documented by each vendor:

#### Technical Audit Trail & Vendor Documentation Claims
- **`[COOKIE & IP HANDLING — {t_target['name'].upper()}]`** {sanitize_third_party_text(t_target.get('vendor_claim_summary', ''), 220)} **Data Retention:** {format_prudent_retention(t_target)} — [Official Source &rarr;]({target_src})
- **`[COOKIE & IP HANDLING — {focus_name.upper()}]`** {sanitize_third_party_text(ctx.get('vendor_claim_summary', ''), 220)} **Data Retention:** {format_prudent_retention(ctx)} — [Official Source &rarr;]({focus_src})
- **`[ENTERPRISE & SELF-HOSTED OPTION — {t_decoy['name'].upper()}]`** {sanitize_third_party_text(t_decoy.get('vendor_claim_summary', ''), 220)} **Data Retention:** {format_prudent_retention(t_decoy)} — [Official Source &rarr;]({sanitize_external_url(t_decoy.get('source_url', ''))})
"""

    condensed_aida_brief = "\n\n".join(aida_lines)
    blockquote_aida = "> " + condensed_aida_brief.replace("\n\n", "\n> \n> ")

    content = f"""![{blueprint['title']}]({image_url} "Technical specification comparison and verification audit for {blueprint['keyword']}.")

## Executive Technical Summary

{blockquote_aida}

---

{middle_section}

## Side-by-Side Technical Specification Matrix (3 Verified Solutions)

The following table compares three real-world analytics platforms from our curated technical specification matrix. All specifications reflect what each vendor states in its official documentation as of the indicated verification date:

{decoy_table_md}

{sources_notes_md}

## Architectural Considerations for Engineering & DPO Teams

Deploying or migrating a web analytics stack involves both software engineering constraints (script weight, Content Security Policy headers, Single-Page Application routing) and organizational governance. According to the vendor documentation cited above, cookieless analytics platforms aim to reduce client-side storage complexity by avoiding persistent cross-session identifiers.

However, technical configurations alone do not replace a formal legal assessment. Engineering teams should review each vendor's Data Processing Agreement (DPA), sub-processor list, and server region documentation (`source_url`) alongside their Data Protection Officer (DPO) or legal counsel.
"""
    return content, condensed_aida_brief


def quality_gate_ymyl(blueprint, markdown_content, aida_brief, freshness_threshold_days):
    """Quality Gate YMYL étendue à 3 états ('index', 'noindex', 'skip')."""
    cat = blueprint.get("page_category", "")
    tools = blueprint.get("tools_used", [])
    ctx = blueprint.get("context_item")

    if len(tools) < 3:
        return "skip", "Moins de 3 outils réels vérifiés dans le comparatif (Decoy incomplet)."

    required_tool_fields = ["cookies_by_default", "ip_handling", "server_region", "source_url", "last_verified"]
    for t in tools:
        if t.get("_exemple", False):
            return "skip", f"Outil '{t.get('name')}' encore marqué _exemple: true."
        for req_key in required_tool_fields:
            if not t.get(req_key):
                return "skip", f"Champ obligatoire '{req_key}' manquant pour l'outil '{t.get('name')}'."
        if not sanitize_external_url(t.get("source_url", "")):
            return "skip", f"URL de source officielle invalide pour l'outil '{t.get('name')}'."

    if cat == "framework_guide" and isinstance(ctx, dict):
        if ctx.get("_exemple", False):
            return "skip", f"Framework '{ctx.get('name')}' encore marqué _exemple: true."
        if not sanitize_external_url(ctx.get("official_docs_url", "")):
            return "skip", f"official_docs_url manquante pour le framework '{ctx.get('name')}'."

    if cat == "regulatory_watch":
        reg_list = ctx if isinstance(ctx, list) else []
        if not reg_list:
            return "skip", "Aucune publication officielle issue des flux RSS disponible."
        for item in reg_list:
            if item.get("_exemple", False):
                return "skip", f"Entrée RSS '{item.get('id')}' marquée _exemple: true (interdit)."
            if not sanitize_external_url(item.get("official_url", "")):
                return "skip", f"URL officielle manquante sur l'entrée RSS '{item.get('id')}'."
            if not sanitize_external_url(item.get("license_url", "")):
                return "skip", f"URL de licence (license_url) manquante sur l'entrée RSS '{item.get('id')}'."
            if not item.get("attribution_text"):
                return "skip", f"Mention d'attribution obligatoire manquante sur l'entrée RSS '{item.get('id')}'."
            if item.get("authority_id") == "cnil-en":
                if (item.get("summary_short") or "").strip() != "":
                    return "skip", f"Violation CC-BY-ND 4.0 FR : summary_short non vide sur '{item.get('id')}'."
                if "Source : CNIL" not in item.get("attribution_text", "") or "CC-BY-ND" not in item.get("attribution_text", ""):
                    return "skip", f"Attribution CNIL CC-BY-ND 4.0 FR incomplète sur '{item.get('id')}'."

    lower_md = markdown_content.lower()
    for pattern in FORBIDDEN_YMYL_PHRASES:
        if re.search(pattern, lower_md):
            return "skip", f"Expression juridique interdite détectée par regex YMYL : '{pattern}'."

    if "not legal advice" not in lower_md:
        return "skip", "Avertissement YMYL 'Not Legal Advice' manquant dans le contenu."

    max_age_found = 0
    oldest_entity_name = ""
    entities_to_check = list(tools)
    if isinstance(ctx, dict) and ctx.get("last_verified"):
        entities_to_check.append(ctx)

    for ent in entities_to_check:
        age = compute_verification_age_days(ent.get("last_verified", ""))
        if age > max_age_found:
            max_age_found = age
            oldest_entity_name = ent.get("name", "Entité")

    if max_age_found > freshness_threshold_days:
        return (
            "noindex",
            f"Spécification expirée : '{oldest_entity_name}' vérifié il y a {max_age_found} jours "
            f"(seuil max : {freshness_threshold_days} jours). Mis en noindex."
        )

    if cat == "framework_guide" and isinstance(ctx, dict):
        if ctx.get("_a_verifier", False) and not ctx.get("csp_directive"):
            return (
                "noindex",
                f"Sujet '{ctx.get('id')}' marqué _a_verifier: true avec paramètre primaire 'csp_directive' à null "
                f"(remplacé par une formulation prudente et routé en noindex jusqu'à vérification manuelle)."
            )

    brief_words = len(re.findall(r"\b\w+\b", aida_brief))
    total_words = len(re.findall(r"\b\w+\b", markdown_content))

    if total_words < ARTICLE_MIN_TOTAL_WORDS:
        return "noindex", f"Contenu trop court ({total_words} mots < {ARTICLE_MIN_TOTAL_WORDS}), mis en noindex."

    if brief_words < AIDA_BRIEF_MIN_WORDS or brief_words > AIDA_BRIEF_MAX_WORDS:
        logger.warning(
            f"[Quality Gate] Brief AIDA pour '{blueprint['slug']}' hors cible idéale "
            f"({brief_words} mots ; cible {AIDA_BRIEF_MIN_WORDS}-{AIDA_BRIEF_MAX_WORDS})."
        )

    ambiguous_tools = [t["id"] for t in tools if t.get("_a_verifier", False)]
    ambig_note = (
        f", champs secondaires null remplacés par formulations prudentes sur {ambiguous_tools}"
        if ambiguous_tools else ""
    )

    return (
        "index",
        f"Conforme YMYL & Licences ({len(tools)} outils vérifiés, fraîcheur max {max_age_found}j <= {freshness_threshold_days}j, "
        f"{total_words} mots{ambig_note})."
    )


def build_frontmatter_sources_and_attributions(blueprint):
    """Construit sources_list et attributions_list pour les templates Hugo."""
    tools = blueprint.get("tools_used", [])
    ctx = blueprint.get("context_item")
    cat = blueprint.get("page_category", "")

    sources_list = []
    seen = set()
    for t in tools:
        t_id = t.get("id", "")
        if t_id and t_id not in seen:
            seen.add(t_id)
            sources_list.append({
                "name": t.get("name", ""),
                "url": sanitize_external_url(t.get("source_url", "")),
                "last_verified": t.get("last_verified", "2026-11-09"),
                "ambiguous_fields": bool(t.get("_a_verifier", False))
            })

    if cat == "framework_guide" and isinstance(ctx, dict):
        sources_list.append({
            "name": f"{ctx.get('name', 'Framework')} Official Documentation",
            "url": sanitize_external_url(ctx.get("official_docs_url", "")),
            "last_verified": ctx.get("last_verified", "2026-11-09"),
            "ambiguous_fields": bool(ctx.get("_a_verifier", False))
        })

    attributions_list = []
    if cat == "regulatory_watch" and isinstance(ctx, list):
        seen_auth = set()
        for item in ctx:
            auth_id = item.get("authority_id", "")
            if auth_id and auth_id not in seen_auth:
                seen_auth.add(auth_id)
                attributions_list.append({
                    "authority_id": auth_id,
                    "authority_name": item.get("authority_name", ""),
                    "license": item.get("license", ""),
                    "license_url": sanitize_external_url(item.get("license_url", "")),
                    "attribution_text": item.get("attribution_text", ""),
                    "extraction_date": item.get("extraction_date_ddmmyyyy", "")
                })

    has_ambiguous = any(t.get("_a_verifier", False) for t in tools) or (
        isinstance(ctx, dict) and bool(ctx.get("_a_verifier", False))
    )

    return sources_list, attributions_list, has_ambiguous


def compute_legacy_title_slug(title_str):
    """
    Calcule l'ancienne URL générée par Hugo à partir du title (lorsque slug n'était pas dans le Frontmatter)
    afin de l'ajouter dans 'aliases' et éviter tout 404 sur les onglets déjà ouverts dans le navigateur.
    """
    s = title_str.lower()
    s = re.sub(r"[^a-z0-9.]+", "-", s).strip("-")
    return f"/{s}/"


def create_or_update_post(blueprint, status_seo, markdown_content, image_url, is_dry_run):
    """Crée ou met à jour un fichier Markdown de manière idempotente avec son vrai 'slug' Hugo."""
    slug = blueprint["slug"]
    file_path = os.path.join(POSTS_DIR, f"{slug}.md")
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    target_id = blueprint.get("target_tool_id", "simple-analytics")
    aff = AFFILIATE_CONFIG.get(target_id, AFFILIATE_CONFIG["simple-analytics"])
    tools = blueprint["tools_used"]
    latest_verif = max(t.get("last_verified", "2026-11-09") for t in tools)
    primary_source_url = sanitize_external_url(tools[0].get("source_url", ""))

    sources_list, attributions_list, has_ambiguous = build_frontmatter_sources_and_attributions(blueprint)
    pricing_disclaimer = (
        f"Prices as of {latest_verif}; tax/VAT treatment may vary by jurisdiction at checkout. "
        f"When a price displays 'See vendor pricing page', VAT treatment or currency equivalence "
        f"was not explicitly stated on the primary pricing page."
    )

    legacy_alias = compute_legacy_title_slug(blueprint["title"])
    aliases = [legacy_alias] if legacy_alias != f"/{slug}/" else []

    new_metadata = {
        "title": blueprint["title"],
        "slug": slug,
        "aliases": aliases,
        "description": blueprint["description"],
        "date": current_time,
        "lastmod": current_time,
        "seo_index": status_seo,
        "type_page": blueprint["page_category"],
        "keyword": blueprint["keyword"],
        "image": image_url,
        "last_verified": latest_verif,
        "official_source_url": primary_source_url,
        "compared_tools_count": len(tools),
        "has_ambiguous_fields": has_ambiguous,
        "pricing_disclaimer": pricing_disclaimer,
        "sources_list": sources_list,
        "attributions_list": attributions_list,
        "not_legal_advice": "Technical comparison only — Not legal advice.",
        "outil_cible": aff["nom"],
        "proposition_valeur": aff["proposition"],
        "lien_affiliation_principal": aff["url"],
        "texte_bouton": aff["btn_texte"],
        "spec_badge_1": aff["spec_badge_1"],
        "spec_badge_2": aff["spec_badge_2"],
        "spec_badge_3": aff["spec_badge_3"]
    }

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        if (
            (post.content or "").strip() == markdown_content.strip()
            and post.metadata.get("slug") == slug
            and post.metadata.get("keyword") == blueprint["keyword"]
            and post.metadata.get("seo_index") == status_seo
            and post.metadata.get("last_verified") == latest_verif
            and post.metadata.get("lien_affiliation_principal") == aff["url"]
            and post.metadata.get("image") == image_url
            and post.metadata.get("pricing_disclaimer") == pricing_disclaimer
            and post.metadata.get("sources_list") == sources_list
            and post.metadata.get("attributions_list") == attributions_list
        ):
            logger.debug(f"[Idempotent] Aucun changement pour {slug}. Fichier ignoré.")
            return False

        logger.info(f"Mise à jour de la page existante : {slug}.md (slug={slug})")
        preserved_date = post.metadata.get("date", current_time)
        post.metadata.update(new_metadata)
        post.metadata["date"] = preserved_date
        post.content = markdown_content
    else:
        logger.info(f"Création d'une nouvelle page A3 : {slug}.md (slug={slug})")
        post = frontmatter.Post(markdown_content, **new_metadata)

    if not is_dry_run:
        os.makedirs(POSTS_DIR, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

    return True


def main():
    parser = argparse.ArgumentParser(description="Générateur programmatique Vecteur A3 (AIDA + Quality Gate YMYL & Licences).")
    parser.add_argument("--dry-run", action="store_true", help="Simule l'exécution sans écrire de fichiers.")
    parser.add_argument("--verbose", action="store_true", help="Affiche les logs détaillés.")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES_PER_RUN,
        help=f"Nombre maximal de pages créées/mises à jour par exécution (défaut: {DEFAULT_MAX_PAGES_PER_RUN})."
    )
    parser.add_argument(
        "--freshness-days",
        type=int,
        default=DEFAULT_FRESHNESS_THRESHOLD_DAYS,
        help=f"Seuil maximal d'ancienneté de last_verified en jours avant passage en noindex (défaut: {DEFAULT_FRESHNESS_THRESHOLD_DAYS})."
    )
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not args.dry_run:
        ensure_default_cover_exists()

    data = load_privacy_data(DATA_FILE)
    freshness_days = args.freshness_days or data.get("metadata", {}).get("freshness_threshold_days", 90)
    blueprints = build_page_blueprints(data)

    if not blueprints:
        logger.critical("ÉCHEC CRITIQUE : Aucun plan de page (blueprint) n'a pu être construit. Arrêt (exit 1).")
        sys.exit(1)

    pages_indexed = 0
    pages_noindex = 0
    pages_skipped = 0

    logger.info(f"=== DÉBUT QUALITY GATE YMYL & LICENCES (Seuil fraîcheur: {freshness_days}j | Drip max: {args.max_pages} pages) ===")

    for bp in blueprints:
        if pages_indexed + pages_noindex >= args.max_pages:
            logger.info(f"Limite de Drip Publishing atteinte ({args.max_pages} pages traitées pour cette exécution).")
            break

        image_url = resolve_topic_image(bp["slug"])
        markdown_content, aida_brief = generate_aida_markdown_a3(bp, image_url)
        status_seo, reason = quality_gate_ymyl(bp, markdown_content, aida_brief, freshness_days)

        if status_seo == "skip":
            logger.warning(f"[REJETÉ - SKIP] {bp['slug']} : {reason}")
            pages_skipped += 1
            continue

        logger.info(f"[ACCEPTÉ - {status_seo.upper()}] {bp['slug']} : {reason}")
        changed = create_or_update_post(bp, status_seo, markdown_content, image_url, args.dry_run)

        if changed:
            if status_seo == "index":
                pages_indexed += 1
            else:
                pages_noindex += 1

    logger.info("=== RAPPORT FINAL DE GÉNÉRATION VECTEUR A3 ===")
    logger.info(f"Pages créées/mises à jour (INDEX)   : {pages_indexed}")
    logger.info(f"Pages créées/mises à jour (NOINDEX) : {pages_noindex}")
    logger.info(f"Pages rejetées (SKIP YMYL)          : {pages_skipped}")
    if args.dry_run:
        logger.info("Mode --dry-run actif : Aucun fichier Markdown n'a été écrit sur le disque.")


if __name__ == "__main__":
    main()




