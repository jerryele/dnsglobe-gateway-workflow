# Changelog

## v1.0.1

- Added a "Majority answer" info box below the map, showing dig-style detail (name/ttl/class/type/data, one line per record, in server order) for a representative resolver from the majority group - so a CNAME chain reads the way `dig` would print it, not just as a flat value list.

## v1.0.0

Initial release.

- DNS propagation check against 34 built-in public resolvers (A/AAAA/CNAME/MX/NS/TXT/SOA), with auto-refresh until fully propagated.
- Round-robin-safe answer grouping; SERVFAIL/REFUSED/timeout classified separately from real propagation signals.
- World map + sortable results table + NS Server List panel (all sortable).
- Fully customizable resolver list: bulk import (.txt/.csv), manual add with live connectivity test before adding, per-resolver enable/disable, delete, delete-all, and restore-to-defaults.
- Custom resolver list persists across restarts and code redeploys.
