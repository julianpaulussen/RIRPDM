"""Run SPARQL queries against the live GraphDB endpoint.

Reasoning is whatever the GraphDB repository ruleset provides (use
RDFS-Plus or OWL2-RL when creating the `rirpdm` repo so subclass /
inverse / functional axioms are inferred).

Usage:
    python3 scripts/query_endpoint.py                 # run every sparql/*.rq
    python3 scripts/query_endpoint.py sparql/cq00.rq  # run one query
"""
import sys
from pathlib import Path
from typing import Any, cast

from SPARQLWrapper import SPARQLWrapper, JSON
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

ENDPOINT = "http://localhost:7200/repositories/rirpdm"
SPARQL_DIR = Path(__file__).parent.parent / "sparql"


def load_queries(only: Path | None = None) -> dict[str, str]:
    if only is not None:
        return {only.stem.upper(): only.read_text()}
    return {f.stem.upper(): f.read_text() for f in sorted(SPARQL_DIR.glob("*.rq"))}


def print_table(vars_: list[str], bindings: list[dict[str, Any]]) -> None:
    rows = [[row.get(v, {}).get("value", "") for v in vars_] for row in bindings]
    widths = [len(v) for v in vars_]
    for r in rows:
        widths = [max(w, len(c)) for w, c in zip(widths, r)]
    sep = "  "
    print(sep.join(v.ljust(w) for v, w in zip(vars_, widths)))
    print(sep.join("-" * w for w in widths))
    for r in rows:
        print(sep.join(c.ljust(w) for c, w in zip(r, widths)))
    print(f"  ({len(rows)} row(s))")


def run_queries(only: Path | None = None) -> None:
    sparql = SPARQLWrapper(ENDPOINT)
    sparql.setReturnFormat(JSON)

    for title, query in load_queries(only).items():
        print(f"\n{'='*60}\n{title}\n{'='*60}")
        sparql.setQuery(query)
        try:
            results = cast(dict[str, Any], sparql.query().convert())
        except (SPARQLWrapperException, OSError) as exc:
            print(f"  ERROR querying {ENDPOINT}: {exc}")
            print("  Is GraphDB running and the 'rirpdm' repository loaded?")
            return

        bindings = results["results"]["bindings"]
        if not bindings:
            print("  (no results)")
            continue
        print_table(results["head"]["vars"], bindings)


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    run_queries(target)
