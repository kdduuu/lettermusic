# F09.16 — Cover first

User feedback after F09.15: album and artist art must breathe, without outer cards. Remove album-gallery, search, library/history, list-item, profile shelf and trending-album frames; retain review/activity and collection cards as social content, where the thumbnail is supporting information. Collection identity unchanged; align title, count and author within a single card with more spacing. Unify every displayed rating with the existing site accent through --lm-rating. No API, schema, dependencies or data changes. Validate browser and CI before merging.

## Follow-up
Remove outer review cards everywhere: Discover, Reviews, Community review activity, profile, album detail and Library reviews. Keep equal review hierarchy, subtle separators, red ratings and existing collection cards. Other Community activity and album interaction panel remain unchanged.

## Final visual adjustments
Unify every Recent activity item into an unboxed feed with equal alignment and subtle separators; preserve the right Community column. History becomes a date-grouped chronological diary (America/Sao_Paulo, same timezone as before), one row per listening event with the recorded local time. Keep API ordering, pagination, repeated plays and other Library tabs unchanged. A date may continue on the next page. No backend changes.
