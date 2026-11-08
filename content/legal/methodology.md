---
# Chemin exact : content/legal/methodology.md
title: "Technical Audit Methodology, Primary Sources & License Governance"
description: "How we verify web analytics technical specifications, enforce our 90-day freshness standard, and comply with European Data Protection Authority reuse licenses."
date: 2026-10-26T00:00:00Z
lastmod: 2026-10-28T00:00:00Z
seo_index: "index"
---

## 1. Primary Vendor Documentation & 90-Day Freshness Standard

Unlike automated aggregators that repeat unverified marketing claims, our technical comparisons evaluate documented software architecture parameters audited directly against each vendor's official technical documentation, security whitepapers, and data policies.

| Analytics Platform | Architectural Category | Primary Official Documentation | Last Verified | Pricing & Retention Verification Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Simple Analytics** | Managed EU Cookieless Cloud | [Security & Ownership Docs &rarr;](https://docs.simpleanalytics.com/data-security-and-ownership) | **2026-10-27** | Starting price displays a prudent checkout notice because VAT inclusion is not stated on the primary pricing page. |
| **Plausible Analytics** | Open-Source Cookieless Analytics | [Official Data Policy &rarr;](https://plausible.io/data-policy) | **2026-10-27** | All primary technical and pricing parameters confirmed (VAT excluded and calculated at checkout by Paddle). |
| **Fathom Analytics** | Privacy-Focused Cloud Analytics | [Technical Data Routing &rarr;](https://usefathom.com/data) | **2026-10-27** | EU Data Isolation proxy routing confirmed; aggregate retention ceiling and checkout VAT treatment carry a prudent verification notice. |
| **Piwik PRO** | Enterprise Analytics & CMP Suite | [Privacy & Security Docs &rarr;](https://piwik.pro/privacy-security/) | **2026-10-27** | Cookie and IP masking modes confirmed; starting price carries a prudent checkout notice regarding VAT treatment. |
| **Matomo Analytics** | Self-Hosted & Cloud Analytics | [Privacy Configuration FAQ &rarr;](https://matomo.org/faq/general/configure-privacy-settings-in-matomo/) | **2026-10-27** | On-Premise and Cloud technical settings confirmed; Cloud entry pricing displays a currency comparison note (USD vs. EUR excl. tax). |
| **Google Analytics 4** | Traditional Behavioral Baseline | [EU Data & Privacy Help &rarr;](https://support.google.com/analytics/answer/12017362) | **2026-10-27** | Standard tier is free ($0); Google Analytics 360 enterprise tier is available by custom contract quote only. |

### Editorial Quality Gate & Prudent Disclosure Rules
* **90-Day Freshness Requirement:** Every software specification and framework guide on this portal is tied to an explicit verification date. If any underlying technical specification exceeds **90 days** without human re-verification against the vendor's primary documentation, the affected report is automatically removed from search engine indexing until re-audited.
* **Prudent Pricing & Tax Notices:** Whenever a vendor's pricing page does not explicitly state whether listed amounts include or exclude Value Added Tax (VAT), or when multi-currency tables differ, we omit unconfirmed figures and direct readers to the vendor's official pricing page (*"Prices as of verification date; tax treatment may vary at checkout"*).
* **Sandbox & CSP Verification:** When a platform executes third-party scripts inside an isolated environment (such as Shopify's *Custom Web Pixels* sandbox), we document the architectural isolation and withhold search indexing until all third-party Content Security Policy (CSP) domains are verified in primary documentation.

---

## 2. Frontend Framework Integration Research

Our implementation guides evaluate script loading strategies, Single-Page Application (SPA) route transition tracking, and Content Security Policy (CSP) directives across six modern web architectures audited on **2026-10-27**:
* **Next.js (App Router)** — [Official Script Optimization Guide](https://nextjs.org/docs/app/guides/scripts)
* **React 19 (Vite / SPA & SSR)** — [Official React DOM `<script>` Reference](https://react.dev/reference/react-dom/components/script)
* **Astro (Static, Islands & View Transitions)** — [Official Client-Side Scripts Guide](https://docs.astro.build/en/guides/client-side-scripts/)
* **Vue 3 (Vite / SPA & Nuxt SSR)** — [Official Vue Integration Documentation](https://docs.simpleanalytics.com/install-simple-analytics-with-vue)
* **Remix (Full-Stack SSR & Client Router)** — [Official Remix `<Scripts />` Documentation](https://v2.remix.run/docs/components/scripts/)
* **Shopify (Online Store 2.0 & Web Pixels API)** — [Official Shopify Web Pixels API Reference](https://shopify.dev/docs/api/web-pixels-api)

**Independent Curated Research (Zero GPL-3.0 Contamination & Zero HTML Scraping):**
Rather than relying on automated technology-fingerprinting libraries whose active community forks are licensed under the restrictive **GNU General Public License v3.0 (GPL-3.0)**, our engineering team maintains an independent, manually verified matrix of official framework integration patterns without automated HTML scraping.

---

## 3. Data Protection Authority (DPA) Feeds & Reuse Licenses

To help engineering and privacy teams monitor primary regulatory publications without issuing legal interpretations, our regulatory digest syndicates official XML feeds from European supervisory authorities.

### A. Active Institutional Syndication Sources (Verified on `2026-10-28`)

| Supervisory Authority | Official Syndication Feed | Reuse License & Attribution Standard |
| :--- | :--- | :--- |
| **European Data Protection Board (EDPB — News)** | [EDPB Official News Feed &rarr;](https://www.edpb.europa.eu/feed/news_en) | [EDPB Legal Notice &rarr;](https://www.edpb.europa.eu/copyright_en) — Reuse is authorized with source acknowledgement provided the original meaning is not distorted. We publish the exact unmodified title, publication date, direct institutional link, and full EDPB attribution. |
| **European Data Protection Board (EDPB — Publications)** | [EDPB Guidelines Feed &rarr;](https://www.edpb.europa.eu/feed/publications_en) | [EDPB Legal Notice &rarr;](https://www.edpb.europa.eu/copyright_en) — Publishes official guidelines and Article 64 opinions with exact unmodified titles, dates, direct portal links, and mandatory source attribution. |
| **CNIL (French Data Protection Authority — English)** | [CNIL Official English Feed &rarr;](https://www.cnil.fr/en/rss.xml) | [CC-BY-ND 4.0 FR License &rarr;](https://creativecommons.org/licenses/by-nd/4.0/deed.fr) — In strict compliance with the *NoDerivatives* clause of the [CNIL Legal Notice](https://www.cnil.fr/fr/mentions-legales), we apply **zero text modification or truncation**: we display only the exact official title, direct CNIL link, extraction date (`DD/MM/YYYY`), license link, and mandatory credit (`Source : CNIL – https://www.cnil.fr`). |

### B. Documented Scope & Institutional Feed Limitations

In accordance with our strict **Zero HTML Scraping** policy and infrastructure Acceptable Use Policies, we never bypass institutional firewalls or scrape web pages when an XML feed is unavailable:

| Supervisory Authority | Examined Portal | Verification Status (`2026-10-28`) | Operational Policy |
| :--- | :--- | :--- | :--- |
| **EDPS** (European Data Protection Supervisor) | [EDPS Official Portal &rarr;](https://www.edps.europa.eu/_en) | Automated cloud runner requests receive `HTTP 403 Forbidden` from the institutional firewall. | Excluded from automated syndication; we never attempt to circumvent institutional firewall rules. |
| **UK ICO** (Information Commissioner's Office) | [ICO RSS Feeds Notice &rarr;](https://ico.org.uk/global/rss-feeds/news-and-blogs/) | RSS syndication is officially disabled by the ICO following a portal redesign (returns an HTML notice page). | Excluded from automated XML syndication; no HTML scraping is performed. |
| **Irish DPC** (Data Protection Commission — Ireland) | [DPC Latest News Portal &rarr;](https://www.dataprotection.ie/en/news-media/latest-news) | No public RSS or Atom XML feed is exposed on the official portal. | Irish national decisions and Article 64 opinions are covered through the official EDPB national news and publications feeds. |

---

## 4. Telemetry Transparency, Affiliate Disclosure & Contact

<!-- [À VÉRIFIER / ADAPTER DANS hugo.toml : Confirmer l'outil d'analytics réellement activé sur votre domaine final et remplacer l'adresse e-mail de contact ci-dessous] -->
* **Our Own Analytics Architecture:** In the interest of technical transparency, this portal is configured to use **Plausible Analytics** — one of the cookieless, European-hosted web analytics solutions evaluated in our comparisons — to measure aggregate pageviews and outbound documentation clicks without browser cookies.
* **Single-CTA & Three-Option Comparison Policy:** Each technical report features a single primary partner Call-To-Action clearly marked as a sponsored referral link in accordance with **FTC 16 CFR Part 255**. Every comparison table evaluates **three real, verified software solutions** side by side and never uses fictitious competitors or fabricated star ratings.
* **Corrections & Editorial Contact:** Legal and methodology disclosures are provided for technical transparency and should be reviewed alongside qualified legal counsel before commercial deployment. To report an updated vendor specification or pricing change, contact our editorial team at **compliance-contact@privacy-analytics-intel.privacyanalyticsintel.com**.
