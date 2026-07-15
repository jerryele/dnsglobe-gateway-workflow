# DNSGlobe for BlueCat Gateway

A [BlueCat Gateway](https://docs.bluecatnetworks.com/r/Gateway-Administration-Guide) workflow that checks DNS record propagation across dozens of public resolvers worldwide, right from your Gateway instance — a world map, a sortable results table, and full control over which resolvers you query.

Query every resolver in your list concurrently, group their answers (round-robin-safe — resolvers serving different subsets of one healthy pool are treated as agreeing, not diverging), and see at a glance whether a record has fully propagated.

## Features

- **34 built-in public resolvers** across Google, Cloudflare, Quad9, OpenDNS, and regional providers spanning North America, Europe, Russia/Middle East, East Asia, and the southern hemisphere.
- **Propagation check** for A, AAAA, CNAME, MX, NS, TXT, and SOA records, with auto-refresh until every responding resolver agrees.
- **Smart answer grouping** — SERVFAIL (a real "this domain is broken" signal) is distinguished from REFUSED/timeout (says nothing about propagation, excluded from the percentage).
- **World map** of every resolver, colored by agreement status, with hover detail.
- **Fully customizable resolver list**:
  - Import resolvers in bulk from a `.txt` (one IP per line, optional name) or `.csv` (`name,ip,location,lat,lon`, header row optional) file.
  - Add a single resolver by hand — it's live-tested with a real DNS query before being added, so you never end up with a dead entry silently sitting in your list.
  - Enable/disable individual resolvers, or bulk select all/none, without losing them from the list.
  - Delete individual resolvers, or clear the whole list.
  - **Restore defaults** at any time to get back the original 34 — nothing is lost by experimenting.
- Sortable columns everywhere (results table and the NS Server List panel).

## Requirements

- BlueCat Gateway (tested on 25.1.x).
- [`dnspython`](https://pypi.org/project/dnspython/) >= 2.6.0 and `flask_restx` — both are already bundled with the Gateway runtime on modern versions; see `workflows/dnsglobe/requirements.txt`.
- Outbound UDP/TCP port 53 access from the Gateway host to the public internet (the whole point of the tool is querying resolvers out there).

## Installation

1. Copy `workflows/dnsglobe` from this repo into `<bluecat_gateway>/workflows/` on your Gateway host (e.g. via `docker cp` into the Gateway container, or directly onto the host path Gateway's workflows directory is mounted from).
2. Restart the Gateway container so it picks up the new workflow.
3. In the Gateway UI, go to **Administration → Workflow Permissions** and grant the `dnsglobe_page` permission (under the `dnsglobe` workflow) to whichever user groups should see it.
4. DNSGlobe now appears in the Gateway navigation menu.

## Configuration

A custom resolver list (from Import / Add / Delete / Restore defaults) is persisted at `/bluecat_gateway/dnsglobe_data/resolvers.json` inside the container — outside the workflow's own code directory, so redeploying a code update never wipes your custom list. Deleting that file (or clicking **Restore defaults** in the UI) reverts to the built-in 34.

## Credits

The propagation-check concept, the built-in resolver list, and the answer-classification/grouping logic are ported from [514-labs/dnsglobe](https://github.com/514-labs/dnsglobe), a terminal UI (Rust) tool doing the same thing on your own machine. This project reimplements that logic natively as a BlueCat Gateway web workflow, adds the fully customizable resolver list, and integrates with Gateway's UI shell. All credit for the original idea and resolver curation goes to that project (MIT licensed).

## Third-party assets

`workflows/dnsglobe/fonts/` bundles [Open Sans](https://fonts.google.com/specimen/Open+Sans) (Apache License 2.0) to match Gateway's native UI typography. Not required — the page falls back to system fonts if the `fonts/` directory is omitted.

## License

MIT — see [LICENSE](LICENSE).
