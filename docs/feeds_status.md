<!-- Chemin exact : docs/feeds_status.md -->
# Data Protection Authority (DPA) RSS Feeds — Audit & Compliance Status

This document records the empirical verification results of official Data Protection Authority (DPA) syndication feeds for the **Vecteur A3** pipeline (`scripts/ingest_privacy.py`).

## 1. Active Official XML Feeds (3/3 Verified HTTP 200 on GitHub Actions Runner)

| Feed ID | Authority | Feed URL | Official Source Page | Runner Test Status & Date | Content-Type & `<description>` | License & Display Policy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`edpb-news`** | European Data Protection Board (EDPB — News) | `https://www.edpb.europa.eu/feed/news_en` | `https://www.edpb.europa.eu/news_en` | **VERIFIED (`HTTP 200`)** on `2026-10-28` (GitHub Actions runner `ubuntu-latest`) | `application/rss+xml` (10 items; HTML markup inside `<description>`) | **EDPB Legal Notice** (`https://www.edpb.europa.eu/copyright_en`). Must cite source and not distort original meaning. Default policy: `title_link_attribution_only` (exact title, date, official link, attribution; cleaned excerpt disabled by default). |
| **`edpb-publications`** | European Data Protection Board (EDPB — Guidelines & Publications) | `https://www.edpb.europa.eu/feed/publications_en` | `https://www.edpb.europa.eu/news_en` | **VERIFIED (`HTTP 200`)** on `2026-10-28` (GitHub Actions runner `ubuntu-latest`) | `application/rss+xml` (10 items; `<description>` tag empty or absent) | **EDPB Legal Notice** (`https://www.edpb.europa.eu/copyright_en`). Policy: `title_link_attribution_only`. Empty `<description>` is kept as `""` and never replaced by the title. |
| **`cnil-en`** | CNIL (French Data Protection Authority — English Feed) | `https://www.cnil.fr/en/rss.xml` | `https://www.cnil.fr/fr/mentions-legales` | **VERIFIED (`HTTP 200`)** on `2026-10-28` (GitHub Actions runner `ubuntu-latest`) | `application/rss+xml` (10 items; plain text `<description>`) | **CC-BY-ND 4.0 FR** (`https://creativecommons.org/licenses/by-nd/4.0/deed.fr`). Strict *NoDerivatives* clause: **zero text modification or truncation**. Displays exact unmodified title, official URL, extraction date (`DD/MM/YYYY`), license link, and `Source : CNIL – https://www.cnil.fr`. |

*Note on `https://www.cnil.fr/fr/rss.xml`: Verified `HTTP 200` (`application/rss+xml`, 10 items) on `2026-10-28` from the GitHub Actions runner, but not enabled in production because Vecteur A3 is an English-language publication and `https://www.cnil.fr/en/rss.xml` provides official English titles directly from the CNIL without requiring automated translation under the CC-BY-ND 4.0 FR license.*

---

## 2. Excluded Authorities & Feeds (Documented Reasons & Dates)

In strict compliance with the **GitHub Acceptable Use Policy (AUP)** and our **Zero HTML Scraping** rule, the following feeds and authorities are excluded from `OFFICIAL_DPA_FEEDS`:

| Authority | Examined / Tested URL | Status & Verification Date | Factual Reason for Exclusion | Compliance & Operational Policy |
| :--- | :--- | :--- | :--- | :--- |
| **EDPS** (European Data Protection Supervisor) | `https://www.edps.europa.eu/feed/news_en` (linked from `https://www.edps.europa.eu/_en`) | **EXCLUDED (`HTTP 403 Forbidden`)** — Measured on `2026-10-28` from GitHub Actions runner (`ubuntu-latest`) | The `edps.europa.eu` Web Application Firewall (WAF) returns `HTTP 403 Forbidden` (`text/html`) to Azure/GitHub Actions runner IP ranges. | **Never bypass a WAF or IP block** (no proxies, no spoofed browser headers). Periodically re-check using the same polite, transparent `User-Agent` in read-only mode to see if institutional firewall rules evolve. |
| **ICO** (Information Commissioner's Office — UK) | `https://ico.org.uk/global/rss-feeds/news-and-blogs/` (index at `https://ico.org.uk/global/rss-feeds/`) | **EXCLUDED (Feed Officially Disabled)** — Verified on `2026-10-27` (primary audit) and `2026-10-28` (runner test: `HTTP 200`, `text/html`, 0 XML items) | The ICO returns an HTML page stating: *"The News and blogs RSS is currently unavailable as we've redesigned the way we present news and blogs."* | Do not scrape HTML pages on `ico.org.uk`. Exclude from automated XML ingestion. |
| **DPC** (Data Protection Commission — Ireland) | `https://www.dataprotection.ie/en/news-media/latest-news` and `/publications` | **EXCLUDED (No XML/RSS Feed Exposed)** — Verified on `2026-10-27` (DOM inspection) | The official Irish DPC website exposes no RSS or Atom syndication feed in its headers, body, or footer. | Zero HTML scraping. Irish national decisions and Article 64 opinions are covered indirectly through the official EDPB feeds (`edpb-news` and `edpb-publications`). |
