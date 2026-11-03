---
aliases:
- /cookieless-web-analytics-implementation-guide-for-react-19-vite-spa-ssr/
attributions_list: []
compared_tools_count: 3
date: '2026-10-26T05:43:32Z'
description: Technical integration guide for deploying cookieless web analytics in
  React 19 (Vite / SPA & SSR) (Single-Page Applications (SPA) & B2B Dashboards) with
  CSP headers and routing notes.
has_ambiguous_fields: true
image: /images/default-cover.svg
keyword: React 19 SPA & SSR
last_verified: '2026-10-27'
lastmod: '2026-11-01T03:29:36Z'
lien_affiliation_principal: https://www.simpleanalytics.com/
not_legal_advice: Technical comparison only — Not legal advice.
official_source_url: https://docs.simpleanalytics.com/data-security-and-ownership
outil_cible: Simple Analytics
pricing_disclaimer: Prices as of 2026-10-27; tax/VAT treatment may vary by jurisdiction
  at checkout. When a price displays 'See vendor pricing page', VAT treatment or currency
  equivalence was not explicitly stated on the primary pricing page.
proposition_valeur: Evaluate an EU-hosted, cookieless web analytics layer according
  to vendor technical documentation.
seo_index: index
slug: cookieless-analytics-implementation-react-spa
sources_list:
- ambiguous_fields: true
  last_verified: '2026-10-27'
  name: Simple Analytics
  url: https://docs.simpleanalytics.com/data-security-and-ownership
- ambiguous_fields: true
  last_verified: '2026-10-27'
  name: Fathom Analytics
  url: https://usefathom.com/data
- ambiguous_fields: true
  last_verified: '2026-10-27'
  name: Matomo Analytics
  url: https://matomo.org/faq/general/configure-privacy-settings-in-matomo/
- ambiguous_fields: false
  last_verified: '2026-10-27'
  name: React 19 (Vite / SPA & SSR) Official Documentation
  url: https://react.dev/reference/react-dom/components/script
spec_badge_1: Cookieless by Default (Vendor Docs)
spec_badge_2: EU Server Hosting (Netherlands)
spec_badge_3: No Raw IP Storage
texte_bouton: Explore Simple Analytics & Docs
title: Cookieless Web Analytics Implementation Guide for React 19 (Vite / SPA & SSR)
type_page: framework_guide
---

![Cookieless Web Analytics Implementation Guide for React 19 (Vite / SPA & SSR)](/images/default-cover.svg "Technical specification comparison and verification audit for React 19 SPA & SSR.")

## Executive Technical Summary

> **Architectural Context:** Engineering teams building React 19 (Vite / SPA & SSR) applications frequently evaluate cookieless analytics scripts to minimize client-side bundle overhead and avoid persistent browser storage.
> 
> **Documented Behavior:** According to Simple Analytics and Fathom Analytics technical documentation (last verified on 2026-10-27), pageviews can be recorded via lightweight JavaScript hooks without setting browser cookies by default.
> 
> **Integration Trade-offs:** Unlike full enterprise suites such as Matomo Analytics that bundle tag managers and consent modules, dedicated cookieless scripts focus on aggregate traffic metrics and explicit Content Security Policy (CSP) directives.
> 
> **Verification Step:** Review the React 19 (Vite / SPA & SSR) script integration parameters and official vendor documentation links below, and consult your legal counsel to validate your specific deployment.

---

## Technical Integration Parameters for React 19 (Vite / SPA & SSR)

> **Not Legal Advice:** This technical audit compares software specifications documented by each vendor and does not constitute legal advice or a formal regulatory compliance opinion.

When integrating a web analytics script into **React 19 (Vite / SPA & SSR)** (*Single-Page Applications (SPA) & B2B Dashboards*), developers must account for client-side routing transitions and Content Security Policy (CSP) headers documented by the framework maintainer ([Official React 19 (Vite / SPA & SSR) Documentation](https://react.dev/reference/react-dom/components/script) — *last verified 2026-10-27*):

#### Script Injection & Lifecycle Hook [Official Framework Docs &rarr;](https://react.dev/reference/react-dom/components/script)
- **`[COMPONENT]`** *Script Loading Strategy* — Built-in react-dom (v19.3) `<script src='https://scripts.simpleanalyticscdn.com/latest.js' async={true} />` component (providing both src and async={true} without onLoad/onError enables React automatic `<head>` hoisting and deduplication; defer is not recommended with streaming SSR) or standard async script in index.html
- **`[ROUTING]`** *SPA Pageview Tracking* — Simple Analytics automatically triggers virtual pageviews on SPA History API pushState changes (or via data-mode='hash'); Fathom Analytics supports SPA routing via data-spa='auto' or data-spa='history' on its script tag
- **`[CSP HEADER]`** *Content Security Policy* — `script-src 'self' https://scripts.simpleanalyticscdn.com; connect-src 'self' https://queue.simpleanalyticscdn.com; img-src 'self' https://queue.simpleanalyticscdn.com https://simpleanalyticsbadges.com (supports cryptographic nonce prop on React )`


## Side-by-Side Technical Specification Matrix (3 Verified Solutions)

The following table compares three real-world analytics platforms from our curated technical specification matrix. All specifications reflect what each vendor states in its official documentation as of the indicated verification date:

| Software Solution | Cookies by Default (Vendor Claim) | IP Address Handling | Server Region | Starting Price (As of Verified Date) | Official Source & Verification |
|---|---|---|---|---|---|
| [**Simple Analytics**](https://www.simpleanalytics.com/ "sponsored") | No (Never sets cookies, localStorage, or sessionStorage according to vendor documentation) | Not collected or stored; IP addresses are dropped on every request and replaced with zeros (0.0.0.0) via mm... | European Union (Netherlands via Worldstream and Leaseweb Dutch servers; Bunny CDN via BunnyW... | See vendor pricing page (as of 2026-10-27; tax/tier details vary) | [Vendor Docs](https://docs.simpleanalytics.com/data-security-and-ownership) *(Verified 2026-10-27)* |
| **Fathom Analytics** | No (No tracking cookies used according to vendor documentation) | Combined with User-Agent, site ID, and a daily salt (rotating at midnight UTC) to create a SHA-256 visitor... | EU Data Isolation proxy servers in Germany (Falkenstein, Nuremberg) and Finland (Helsinki) f... | See vendor pricing page (as of 2026-10-27; tax/tier details vary) | [Vendor Docs](https://usefathom.com/data) *(Verified 2026-10-27)* |
| **Matomo Analytics** | Configurable (First-party cookies enabled by default with a 13-month cap in CNIL mode; cooki... | In-memory IP anonymization enabled by default (2 bytes masked by default); configurable to mask 1, 2, 3, or... | European Union (Frankfurt, Germany for Matomo Cloud) or User-Controlled On-Premise server lo... | See vendor pricing page (as of 2026-10-27; tax/tier details vary) | [Vendor Docs](https://matomo.org/faq/general/configure-privacy-settings-in-matomo/) *(Verified 2026-10-27)* |

*Pricing & Tax Notice: Prices and plan parameters are reported as of **2026-10-27**; tax/VAT treatment may vary by jurisdiction at checkout. Where a starting price displays "See vendor pricing page", VAT inclusion/exclusion or multi-currency equivalence was not explicitly stated on the vendor's primary pricing page.*


### Primary Documentation Sources & Verification Notes

- **Simple Analytics** ([Official Documentation](https://docs.simpleanalytics.com/data-security-and-ownership) — *last verified 2026-10-27*): **Data Retention:** 30 days on the Free plan (older data auto-deleted); on paid plans, encrypted data is retained per subscription tier while account is active and permanently deleted 90 days after account deletion (per vendor docs). **Pricing Note:** See vendor pricing page (Free plan at $0 (1 user, 5 sites, 30-day history); Paid plans from $20/month (100k pageviews, 1 user included, +$20/month per additional user, monthly or annual billing with 2 months free; VAT treatment not stated on the pricing page)).
- **Fathom Analytics** ([Official Documentation](https://usefathom.com/data) — *last verified 2026-10-27*): **Data Retention:** See vendor documentation (Daily salt rotates at midnight UTC, but SHA-256 visitor signatures of past events remain stored in the database after midnight UTC and no maximum purge period for aggregate stats is specified in /data). **Pricing Note:** See vendor pricing page (From $15/month (USD, up to 100,000 monthly pageviews and up to 50 sites included, monthly or annual billing with 2 months free; VAT treatment not stated on the pricing page)).
- **Matomo Analytics** ([Official Documentation](https://matomo.org/faq/general/configure-privacy-settings-in-matomo/) — *last verified 2026-10-27*): **Data Retention:** Matomo Cloud Business retains raw visit logs for up to 24 months (capped at 759 days in CNIL compliance mode) and aggregated reports forever; Matomo On-Premise retention is fully configurable by the administrator (per vendor docs). **Pricing Note:** See vendor pricing page (Matomo On-Premise Community is Free (€0 forever; Team bundle from €275/month or €230/month billed annually); Matomo Cloud Business displays two different entry amounts on matomo.org/pricing/ depending on currency/table (USD 26/month excl. tax vs EUR 29/mont...).
- **React 19 (Vite / SPA & SSR) Integration Reference** ([Official Framework Docs](https://react.dev/reference/react-dom/components/script) — *last verified 2026-10-27*).


## Architectural Considerations for Engineering & DPO Teams

Deploying or migrating a web analytics stack involves both software engineering constraints (script weight, Content Security Policy headers, Single-Page Application routing) and organizational governance. According to the vendor documentation cited above, cookieless analytics platforms aim to reduce client-side storage complexity by avoiding persistent cross-session identifiers.

However, technical configurations alone do not replace a formal legal assessment. Engineering teams should review each vendor's Data Processing Agreement (DPA), sub-processor list, and server region documentation (`source_url`) alongside their Data Protection Officer (DPO) or legal counsel.