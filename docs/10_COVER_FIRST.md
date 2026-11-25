# F09.16 — Cover first

User feedback after F09.15: album and artist art must breathe, without outer cards. Remove album-gallery, search, library/history, list-item, profile shelf and trending-album frames; retain review/activity and collection cards as social content, where the thumbnail is supporting information. Collection identity unchanged; align title, count and author within a single card with more spacing. Unify every displayed rating with the existing site accent through --lm-rating. No API, schema, dependencies or data changes. Validate browser and CI before merging.

## Follow-up
Remove outer review cards everywhere: Discover, Reviews, Community review activity, profile, album detail and Library reviews. Keep equal review hierarchy, subtle separators, red ratings and existing collection cards. Other Community activity and album interaction panel remain unchanged.

## Final visual adjustments
Unify every Recent activity item into an unboxed feed with equal alignment and subtle separators; preserve the right Community column. History becomes a date-grouped chronological diary (America/Sao_Paulo, same timezone as before), one row per listening event with the recorded local time. Keep API ordering, pagination, repeated plays and other Library tabs unchanged. A date may continue on the next page. No backend changes.

## Visual freeze candidate — final feedback
Use compact calendar-like day number and abbreviated month/year in History; preserve the underlying events and timezone. User approves the overall visual direction; avoid another broad redesign.

## Next stage: functional completion and final audit
- Implement four manually selected, ordered public profile favorite albums, inspired by Letterboxd. Separate from private Library favorites and recent activity. Persist selection; enforce owner-only editing, maximum four distinct albums and public read contract; add migrations and automated tests as needed. Do not treat this as implemented in F09.16.
- Check secondary text size, contrast, keyboard focus and consistency of controls without reopening visual direction.
- Test realistic large collections, long reviews, empty states, pagination and narrow/mobile viewports.
- Correct discography global ordering and verify release classifications across paginated catalog data.
- Investigate the persistent Next.js development '1 Issue' before release; verify actual cause rather than hiding the indicator.
- Exercise album interactions, half-star ratings, review editing/deletion, repeated listening, list ownership/privacy, account flows and email templates. Run backend and frontend checks, browser validation and deployment review.
