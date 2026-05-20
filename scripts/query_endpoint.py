from pathlib import Path
from typing import Any, cast
from SPARQLWrapper import SPARQLWrapper, JSON

ENDPOINT = "http://localhost:7200/repositories/rirpdo"
SPARQL_DIR = Path(__file__).parent.parent / "sparql"


def load_queries() -> dict[str, str]:
    queries = {}
    for rq_file in sorted(SPARQL_DIR.glob("*.rq")):
        queries[rq_file.stem.upper()] = rq_file.read_text()
    return queries


def run_queries():
    sparql = SPARQLWrapper(ENDPOINT)
    sparql.setReturnFormat(JSON)

    for title, query in load_queries().items():
        print(f"\n{'='*60}")
        print(title)
        print('='*60)

        sparql.setQuery(query)
        results = cast(dict[str, Any], sparql.query().convert())
        bindings = results["results"]["bindings"]

        if not bindings:
            print("  (no results)")
            continue

        vars_ = results["head"]["vars"]
        for row in bindings:
            values = [row.get(v, {}).get("value", "-") for v in vars_]
            print("  " + " | ".join(values))


if __name__ == "__main__":
    run_queries()
