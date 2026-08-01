"""Backfill org:subOrganizationOf for institutions fetch_data_openalex.py emitted.

Usage:
    python3 scripts/fetch_data_ror_relationships.py
    python3 scripts/fetch_data_ror_relationships.py --limit 100
"""
import argparse
import json
import urllib.request
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.namespace import OWL

OPENALEX_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-openalex-sample-data.ttl"
OUT_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-ror-relationships-sample-data.ttl"
ROR_ORG_URL = "https://api.ror.org/organizations/{ror_id}"

RIRPDM = Namespace("http://www.example.org/rirpdm#")
DATA = Namespace("http://www.example.org/rirpdm/data#")
ORG = Namespace("http://www.w3.org/ns/org#")


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)


def read_institutions() -> list[tuple[URIRef, str]]:
    """Load institutions fetch_data_openalex.py emitted, return (IRI, ROR tail) pairs."""
    g = Graph()
    g.parse(OPENALEX_FILE, format="turtle")
    out = []
    for inst in g.subjects(RDF.type, RIRPDM.ResearchInstitution):
        local = str(inst).rsplit("#", 1)[-1]
        if local.startswith("inst_"):
            out.append((inst, local[len("inst_"):]))
    return out


def parent_ror(ror_tail: str) -> tuple[str, str] | None:
    """Return (parent ror tail, parent label) from this institution's ROR record, else None."""
    data = get_json(ROR_ORG_URL.format(ror_id=ror_tail))
    for rel in data.get("relationships", []):
        if rel.get("type", "").lower() == "parent" and rel.get("id"):
            return rel["id"].rstrip("/").rsplit("/", 1)[-1], rel.get("label", rel["id"])
    return None


def build_graph(institutions: list[tuple[URIRef, str]]) -> Graph:
    g = Graph()
    g.bind("rirpdm", RIRPDM)
    g.bind("data", DATA)
    g.bind("org", ORG)

    ontology = URIRef("http://www.example.org/rirpdm/data-ror-relationships")
    g.add((ontology, RDF.type, OWL.Ontology))
    g.add((ontology, RDFS.label, Literal("RIRPDM ROR parent-organisation data", lang="en")))
    g.add((ontology, OWL.imports, URIRef("http://www.example.org/rirpdm")))

    # For each institution, if its ROR record declares a parent, emit the parent and link
    seen_parents: set[str] = set()
    for inst, tail in institutions:
        rel = parent_ror(tail)
        if not rel:
            continue
        parent_tail, label = rel
        parent = DATA["org_" + parent_tail]
        if parent_tail not in seen_parents:
            seen_parents.add(parent_tail)
            g.add((parent, RDF.type, OWL.NamedIndividual))
            g.add((parent, RDF.type, ORG.Organization))
            g.add((parent, RDFS.label, Literal(label, lang="en")))
        g.add((inst, ORG.subOrganizationOf, parent))  # transitive (inherited from ORG vocab)

    return g


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=60, help="institutions to check against ROR")
    args = parser.parse_args()

    institutions = read_institutions()[: args.limit]
    build_graph(institutions).serialize(destination=str(OUT_FILE), format="turtle")
    print(f"Checked {len(institutions)} institutions -> {OUT_FILE}")


if __name__ == "__main__":
    main()
