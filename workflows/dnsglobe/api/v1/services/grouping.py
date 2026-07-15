"""
Answer grouping and majority/propagation summary, ported from the dnsglobe TUI
project's `App::summary` (https://github.com/514-labs/dnsglobe, src/app.rs).

The key idea ported as-is: two resolvers' answers are grouped together when
they share *any* record value, not only when their full value sets are equal.
Round-robin DNS has each resolver caching a different subset of one pool, so
without this a healthy pool would look like N different "answers" instead of
one. Union-find over resolvers with a shared-value edge does this in one pass.
"""
from typing import TypedDict

from .query_engine import QueryOutcome


class Summary(TypedDict):
    done: int
    ok: int
    no_records: int
    servfail: int
    errors: int
    responding: int
    groups: int
    agree: int
    majority_rows: list[bool]
    majority_values: list[str]


def compute_summary(outcomes: list[QueryOutcome]) -> Summary:
    n = len(outcomes)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    first_seen: dict[str, int] = {}
    ok_rows: list[int] = []
    done = ok = no_records = servfail = errors = 0

    for i, outcome in enumerate(outcomes):
        kind = outcome["result"]["kind"]
        done += 1
        if kind == "records":
            ok += 1
            ok_rows.append(i)
            for value in outcome["result"]["values"]:
                other = first_seen.get(value)
                if other is None:
                    first_seen[value] = i
                else:
                    parent[find(i)] = find(other)
        elif kind == "no_records":
            no_records += 1
        elif kind == "servfail":
            servfail += 1
        else:
            errors += 1

    responding = ok + no_records + servfail

    counts: dict[int, int] = {}
    for i in ok_rows:
        root = find(i)
        counts[root] = counts.get(root, 0) + 1
    groups = len(counts)

    # Deterministic majority pick: first (in resolver order) among the largest
    # groups - matters only for display order, never for correctness.
    majority_root = None
    best = 0
    for i in ok_rows:
        root = find(i)
        if counts[root] > best:
            best = counts[root]
            majority_root = root

    agree = 0
    majority_rows = [False] * n
    majority_values: list[str] = []
    if majority_root is not None:
        agree = counts[majority_root]
        union: list[str] = []
        for i in ok_rows:
            if find(i) == majority_root:
                majority_rows[i] = True
                union.extend(outcomes[i]["result"]["values"])
        majority_values = sorted(set(union))

    return {
        "done": done,
        "ok": ok,
        "no_records": no_records,
        "servfail": servfail,
        "errors": errors,
        "responding": responding,
        "groups": groups,
        "agree": agree,
        "majority_rows": majority_rows,
        "majority_values": majority_values,
    }


def row_status(outcome: QueryOutcome, is_majority: bool) -> str:
    """Per-row display status: "ok" | "differs" | "no_records" | "servfail" | "error"."""
    kind = outcome["result"]["kind"]
    if kind == "records":
        return "ok" if is_majority else "differs"
    if kind == "no_records":
        return "no_records"
    return kind  # "servfail" | "error"


def fully_propagated(summary: Summary) -> bool:
    """True once every *responding* resolver agrees - mirrors main.rs's watch-mode
    stop condition. Timeouts/refusals carry no propagation signal, so they don't
    block this."""
    return summary["responding"] > 0 and summary["agree"] == summary["responding"]
