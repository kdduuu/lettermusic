# F09.14 — Editorial finale

Base: F09.13, whose frontend CI passed (run 45526100957). This is a candidate for visual freeze, not a declaration of production readiness.

Direction: a magazine-like masthead, warm neutral graphite, real covers, serif hierarchy, consistent content width, restrained pink accent, no decorative geometry, no invented social content.

Discover: cover-led opening, four sections retained, reviews and list index share an editorial grid at desktop and stack at mobile. Lists display actual public records and distinguish empty/error states.
Reviews: first review leads the page, remaining reviews retain a compact reading grid. No truncation added to the full review feed.
Collections: four deterministic muted ink colors distinguish lists; LM. and numbered collection identity retained on full covers, monogram in compact rows.
Album, artist, profile and list detail: remove unnecessary hero panels; retain existing information, actions and cover-first structure.
Community, search, library, auth, header and shared controls: typography, alignment, navigation, spacing and surfaces harmonized. Catalog grid remains five columns on desktop.
No backend/schema/API changes. No fake records. No extra dependencies. Existing routes remain unchanged.

Pending: CI on this branch, browser validation at 100% and mobile, four public favorites, global discography sorting, email templates, diagnosis of prior Next.js issue, final functional audit and deployment. Do not merge before validation.
