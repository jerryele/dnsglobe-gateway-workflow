# Copyright 2026 BlueCat Networks (USA) Inc. and its affiliates. All Rights Reserved.
"""
REST endpoints for DNSGlobe: the resolver list the map is drawn from, and the
propagation check itself.
"""
from flask import request
from flask_restx import Namespace, Resource

from ..services import grouping, query_engine, resolver_store
from ..services.query_engine import run_check
from ..services.resolver_import import parse as parse_resolvers
from ..services.resolver_import import validate_manual_entry
from ..utils.constants import MAX_DOMAIN_LENGTH, RECORD_TYPES
from ..utils.exceptions import InvalidCheckRequest

check_ns = Namespace("propagation", description="DNS propagation checks")


def _resolver_list_payload() -> dict:
    return {
        "resolvers": resolver_store.get_active(),
        "source": "custom" if resolver_store.is_custom() else "default",
    }


@check_ns.route("/resolvers")
class ResolverList(Resource):
    """The active resolver list (custom import if one exists, else the
    built-in 34), for the map to plot before any check has run."""

    def get(self):
        return _resolver_list_payload(), 200


@check_ns.route("/resolvers/import")
class ResolverImport(Resource):
    """
    Bulk-import a custom resolver list from pasted/uploaded text (.txt or
    .csv - see resolver_import.py for the accepted formats), replacing
    whichever list is currently active. Persists across restarts until reset.

    Body: {"text": "<file contents>"}.
    """

    def post(self):
        payload = request.get_json(silent=True) or {}
        text = payload.get("text", "")
        if not text.strip():
            return {"error": "no content to import"}, 400

        resolvers, errors = parse_resolvers(text)
        if not resolvers:
            return {"error": "no valid resolvers found in the import", "details": errors}, 400

        resolver_store.set_custom(resolvers)
        return {**_resolver_list_payload(), "imported": len(resolvers), "errors": errors}, 200


@check_ns.route("/resolvers/reset")
class ResolverReset(Resource):
    """Discard the custom resolver list and revert to the built-in 34."""

    def post(self):
        resolver_store.reset()
        return _resolver_list_payload(), 200


@check_ns.route("/resolvers/add")
class ResolverAdd(Resource):
    """
    Manually add one resolver: validate its fields, then live-test that it
    actually answers a DNS query before appending it to the active list -
    "confirm success, then add", not add-then-hope. Rejected (400/502) means
    nothing was added or persisted.

    Body: {"name": "", "ip": "...", "location": "", "lat": "", "lon": ""}
    (name/location/lat/lon optional; lat and lon must both be given or both
    left blank).
    """

    def post(self):
        payload = request.get_json(silent=True) or {}
        resolver, error = validate_manual_entry(
            payload.get("name"),
            payload.get("ip"),
            payload.get("location"),
            payload.get("lat"),
            payload.get("lon"),
        )
        if error:
            return {"error": error}, 400

        active = resolver_store.get_active()
        if any(r["ip"] == resolver["ip"] for r in active):
            return {"error": f"{resolver['ip']} is already in the list"}, 400

        ok, detail, elapsed_ms = query_engine.test_resolver(resolver["ip"])
        if not ok:
            return {
                "error": f"{resolver['ip']} did not answer a test DNS query ({detail}) - not added"
            }, 502

        resolver_store.set_custom(active + [resolver])
        return {**_resolver_list_payload(), "added": resolver, "test_elapsed_ms": elapsed_ms}, 200


@check_ns.route("/resolvers/delete")
class ResolverDelete(Resource):
    """Remove one resolver (by IP) from the active list entirely. Unlike
    disabling it (see /resolvers/toggle), this is permanent - the only way
    back is /resolvers/reset or re-adding it. Body: {"ip": "..."}."""

    def post(self):
        payload = request.get_json(silent=True) or {}
        ip = (payload.get("ip") or "").strip()
        if not ip:
            return {"error": "ip is required"}, 400

        active = resolver_store.get_active()
        remaining = [r for r in active if r["ip"] != ip]
        if len(remaining) == len(active):
            return {"error": f"{ip} not found in the list"}, 404
        if not remaining:
            return {"error": "cannot delete the last remaining resolver"}, 400

        resolver_store.set_custom(remaining)
        return _resolver_list_payload(), 200


@check_ns.route("/resolvers/delete_all")
class ResolverDeleteAll(Resource):
    """
    Clear the active list to empty - a deliberate full wipe, not subject to
    /resolvers/delete's "keep at least one" guard. Recover via
    /resolvers/reset (built-in 34) or by importing/adding resolvers fresh.
    """

    def post(self):
        resolver_store.set_custom([])
        return _resolver_list_payload(), 200


@check_ns.route("/resolvers/toggle")
class ResolverToggle(Resource):
    """
    Enable or disable one resolver (by IP) without removing it from the
    list - a disabled resolver stays visible everywhere but is skipped by
    /check (see Check.post). Body: {"ip": "...", "enabled": true|false}.
    """

    def post(self):
        payload = request.get_json(silent=True) or {}
        ip = (payload.get("ip") or "").strip()
        enabled = bool(payload.get("enabled", True))
        if not ip:
            return {"error": "ip is required"}, 400

        active = resolver_store.get_active()
        if not any(r["ip"] == ip for r in active):
            return {"error": f"{ip} not found in the list"}, 404

        updated = [{**r, "enabled": enabled} if r["ip"] == ip else r for r in active]
        resolver_store.set_custom(updated)
        return _resolver_list_payload(), 200


@check_ns.route("/resolvers/set_enabled")
class ResolverSetEnabled(Resource):
    """
    Bulk enable/disable, for "Select all" / "Select none". Body:
    {"enabled": true|false, "ips": [...]} - omit "ips" to apply to every
    resolver currently in the list.
    """

    def post(self):
        payload = request.get_json(silent=True) or {}
        enabled = bool(payload.get("enabled", True))
        ips = payload.get("ips")
        active = resolver_store.get_active()
        target_ips = set(ips) if ips else {r["ip"] for r in active}

        updated = [{**r, "enabled": enabled} if r["ip"] in target_ips else r for r in active]
        resolver_store.set_custom(updated)
        return _resolver_list_payload(), 200


def _validate(payload: dict) -> tuple:
    domain = (payload or {}).get("domain", "").strip().lower()
    record_type = (payload or {}).get("record_type", "A").strip().upper()
    if not domain or len(domain) > MAX_DOMAIN_LENGTH:
        raise InvalidCheckRequest("domain is required")
    if record_type not in RECORD_TYPES:
        raise InvalidCheckRequest(f"record_type must be one of {', '.join(RECORD_TYPES)}")
    return domain, record_type


@check_ns.route("/check")
class Check(Resource):
    """
    Query every *enabled* resolver in the active list for one domain/record-
    type and return each resolver's answer plus the propagation summary.
    Resolvers disabled via /resolvers/toggle are not queried at all, but
    still appear in `rows` (status "disabled") so the table/map keep one row
    per active-list resolver - see the reassembly below.

    Body: {"domain": "example.com", "record_type": "A"} (record_type optional,
    defaults to "A").
    """

    def post(self):
        try:
            domain, record_type = _validate(request.get_json(silent=True))
        except InvalidCheckRequest as e:
            return {"error": str(e)}, 400

        active = resolver_store.get_active()
        enabled = [r for r in active if r.get("enabled", True) is not False]

        outcomes = run_check(domain, record_type, enabled)
        summary = grouping.compute_summary(outcomes)

        enabled_rows = [
            {
                "resolver": outcome["resolver"],
                "result": outcome["result"],
                "elapsed_ms": outcome["elapsed_ms"],
                "status": grouping.row_status(outcome, summary["majority_rows"][i]),
            }
            for i, outcome in enumerate(outcomes)
        ]

        # Reassemble in the *active* list's order/length (not just the
        # enabled subset) so the frontend's resolvers[i] <-> rows[i]
        # correspondence (map hover, statusOf) still holds even though
        # disabled resolvers were never queried.
        rows_by_ip = {row["resolver"]["ip"]: row for row in enabled_rows}
        rows = [
            rows_by_ip.get(r["ip"])
            or {"resolver": r, "result": {"kind": "disabled"}, "elapsed_ms": 0, "status": "disabled"}
            for r in active
        ]

        return {
            "domain": domain,
            "record_type": record_type,
            "rows": rows,
            "summary": summary,
            "fully_propagated": grouping.fully_propagated(summary),
        }, 200
