# F09.15 — Social editorial

Based on F09.14 and user feedback. The Discover mockup from November 12 inspires the feature strip, album shelf, and side-by-side Reviews/Lists. Only real album and list data are used. No fictitious genres, editorial descriptions, likes or notifications. Dark theme and English remain.
- Equal chronological review cards, no artificially promoted first entry.
- Album social actions: explicit listened marker, reversible favorite and listen-later, distinct repeat play; direct half-star rating; review/list editing only on demand. Keep existing server action contracts and errors.
- Collection covers: COLLECTION and number only. Pencil and plus on list album heading; edit on demand, search retains list ID. Owner-only controls unchanged.
- Discography: classify using actual primary and secondary types, grouping results on the current paginated page; existing API type filter applies across the catalog. Date sorting remains per page and is labeled as such. No global date-order claim.
- Discreet cards on social activity, library, lists, search, album grids. Track rows remain rows for scannability. Use symbols for familiar actions with accessible names; preserve text for ambiguous/critical actions.
- No backend/schema/dependency changes. Verify CI and real browser interactions before merge; four profile favorites and remaining deployment checks still pending.
