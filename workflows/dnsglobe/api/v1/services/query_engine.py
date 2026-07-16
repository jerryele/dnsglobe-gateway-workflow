"""
Concurrent DNS propagation queries, ported from the dnsglobe TUI project's
src/dns.rs (https://github.com/514-labs/dnsglobe).

Each resolver is queried directly (no cache, single attempt, no fallback to a
system default) so its own view of the record is what gets measured - the same
principle as the Rust original. Every result is classified into one of four
buckets:

  records     - the resolver answered with data; a real propagation signal.
  no_records  - NXDOMAIN or NOERROR-with-empty-answer; also a real signal
                ("this resolver's view is: nothing here").
  servfail    - the resolver tried to resolve this name and couldn't (broken
                delegation, DNSSEC failure, ...). A statement about the
                *domain*, so it counts as responding and blocks 100% agreement.
  error       - timeout, REFUSED, or a network error. Says nothing about
                propagation, so these are excluded from the percentage.
"""
import asyncio
import time
from typing import Final, TypedDict

import dns.asyncquery
import dns.exception
import dns.message
import dns.rcode
import dns.rdataclass
import dns.rdatatype

from .resolvers import Resolver

QUERY_TIMEOUT: Final[float] = 3.0


class DigRecord(TypedDict):
    """One answer-section line, dig's `name  ttl  class  type  data` format."""

    name: str
    ttl: int
    rdclass: str
    rdtype: str
    data: str


class QueryResult(TypedDict, total=False):
    kind: str  # "records" | "no_records" | "servfail" | "error"
    values: list[str]
    min_ttl: int
    records: list[DigRecord]
    code: str
    message: str


class QueryOutcome(TypedDict):
    resolver: Resolver
    result: QueryResult
    elapsed_ms: int


def _short_error(message: str) -> str:
    """Collapse noisy exception text into a stable short label, same buckets
    the Rust original normalizes to (see dns.rs::short_error)."""
    lower = message.lower()
    if "timed out" in lower or "timeout" in lower:
        return "timeout"
    if "refused" in lower:
        return "refused"
    return message[:60]


def _collect_answers(response: "dns.message.Message", rtype: int) -> QueryResult:
    """Fold an answer section into records/no_records, mirroring
    dns.rs::collect_answers: every rrset's TTL counts toward the minimum (even
    a CNAME hop on the way to the requested type), values are labeled with
    their own type when it differs from what was asked for, then sorted and
    deduped so resolvers serving different subsets of a round-robin pool are
    comparable. `records` keeps the raw per-line detail (name/ttl/class/type/
    data, in the server's original answer-section order) for a dig-style
    display - `values`/`min_ttl` stay the normalized form grouping.py compares
    resolvers with."""
    values: list[str] = []
    records: list[DigRecord] = []
    min_ttl = None
    for rrset in response.answer:
        min_ttl = rrset.ttl if min_ttl is None else min(min_ttl, rrset.ttl)
        rdtype_text = dns.rdatatype.to_text(rrset.rdtype)
        rdclass_text = dns.rdataclass.to_text(rrset.rdclass)
        for rdata in rrset:
            data_text = str(rdata)
            if rrset.rdtype == rtype:
                values.append(data_text)
            else:
                values.append(f"{rdtype_text} {data_text}")
            records.append({
                "name": rrset.name.to_text(),
                "ttl": rrset.ttl,
                "rdclass": rdclass_text,
                "rdtype": rdtype_text,
                "data": data_text,
            })
    values = sorted(set(values))
    if not values:
        return {"kind": "no_records", "code": "empty answer"}
    return {"kind": "records", "values": values, "min_ttl": min_ttl or 0, "records": records}


def _classify(response: "dns.message.Message", rtype: int) -> QueryResult:
    code = response.rcode()
    if code == dns.rcode.NOERROR:
        return _collect_answers(response, rtype)
    if code == dns.rcode.NXDOMAIN:
        return {"kind": "no_records", "code": "NXDOMAIN"}
    if code == dns.rcode.SERVFAIL:
        return {"kind": "servfail"}
    if code == dns.rcode.REFUSED:
        return {"kind": "error", "message": "refused"}
    return {"kind": "error", "message": dns.rcode.to_text(code)}


async def _query_one(server_ip: str, domain: str, rtype: int) -> tuple[QueryResult, int]:
    start = time.monotonic()
    try:
        message = dns.message.make_query(domain, rtype, want_dnssec=False)
        response, _used_tcp = await dns.asyncquery.udp_with_fallback(
            message, server_ip, timeout=QUERY_TIMEOUT
        )
        result = _classify(response, rtype)
    except dns.exception.Timeout:
        result = {"kind": "error", "message": "timeout"}
    except Exception as exc:  # noqa: BLE001 - any transport failure becomes "error"
        result = {"kind": "error", "message": _short_error(str(exc))}
    elapsed_ms = round((time.monotonic() - start) * 1000)
    return result, elapsed_ms


async def _check_async(domain: str, rtype: int, resolvers: list[Resolver]) -> list[QueryOutcome]:
    tasks = [_query_one(r["ip"], domain, rtype) for r in resolvers]
    outcomes = await asyncio.gather(*tasks)
    return [
        {"resolver": resolver, "result": result, "elapsed_ms": elapsed_ms}
        for resolver, (result, elapsed_ms) in zip(resolvers, outcomes)
    ]


def run_check(domain: str, rtype_name: str, resolvers: list[Resolver]) -> list[QueryOutcome]:
    """Query every resolver in `resolvers` for `domain`/`rtype_name` concurrently
    and return one outcome per resolver, in the same order. Synchronous entry
    point for Flask's (WSGI) view functions."""
    rtype = dns.rdatatype.from_text(rtype_name)
    return asyncio.run(_check_async(domain, rtype, resolvers))


def test_resolver(ip: str) -> tuple:
    """
    Live-reachability probe for the manual add-resolver form: fires one A
    query for "example.com" and returns (ok, detail, elapsed_ms).

    Any real DNS response counts as success - including SERVFAIL or NXDOMAIN,
    since those still mean a live DNS server answered us. Only a timeout,
    REFUSED, or transport failure (i.e. `_query_one`'s "error" bucket) means
    it isn't actually usable for propagation checks.
    """
    result, elapsed_ms = asyncio.run(_query_one(ip, "example.com.", dns.rdatatype.A))
    ok = result["kind"] != "error"
    detail = result.get("message") or result["kind"]
    return ok, detail, elapsed_ms
