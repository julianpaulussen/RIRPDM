"""Fetch Research Infrastructures from the ROR API and write them as RDF.

ROR (Research Organization Registry) lists organisations. We ask for the ones
typed "facility" and treat each as a rirpdm:SingleSitedRI.

Facility:
- name
- website (accessPoint)
- country 
- ROR id. 

Usage:
    python3 scripts/fetch_data_ror.py            # 1 page  (~20 facilities)
    python3 scripts/fetch_data_ror.py --pages 3  # 3 pages (~60 facilities)
"""
import argparse
import json
import re
import urllib.request
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.namespace import OWL, DCTERMS

ROR_URL = "https://api.ror.org/organizations?filter=types:facility&page={page}"
OUT_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-ror-sample-data.ttl"

RIRPDM = Namespace("http://www.example.org/rirpdm#")
DATA = Namespace("http://www.example.org/rirpdm/data#")


def slugify(name: str) -> str:
    """Turn a name into a safe IRI fragment: 'MRC Cancer Unit' -> 'MRCCancerUnit'."""
    return re.sub(r"[^A-Za-z0-9]", "", name)


def display_name(item: dict) -> str:
    """ROR gives several names per org; pick the canonical display one."""
    for n in item["names"]:
        # ror_display is human-readable
        if "ror_display" in n["types"]:
            return n["value"]
    return item["names"][0]["value"]


def fetch_facilities(pages: int) -> list[dict]:
    """Download pages of ROR facility records (around 20 per page)."""
    facilities = []
    for page in range(1, pages + 1):
        with urllib.request.urlopen(ROR_URL.format(page=page)) as resp:
            facilities.extend(json.load(resp)["items"])
    return facilities


def build_graph(facilities: list[dict]) -> Graph:
    """Turn ROR facility records into RI + Country individuals."""
    g = Graph()
    g.bind("rirpdm", RIRPDM)
    g.bind("data", DATA)

    # ontology header: this data file imports the RIRPDM ontology it uses
    ontology = URIRef("http://www.example.org/rirpdm/data")
    g.add((ontology, RDF.type, OWL.Ontology))
    g.add((ontology, RDFS.label, Literal("RIRPDM ROR-sourced sample data", lang="en")))
    g.add((ontology, OWL.imports, URIRef("http://www.example.org/rirpdm")))

    countries: dict[str, str] = {}  # country name -> slug, so each country is emitted once

    for item in facilities:
        # slugify the name, because ROR names can contain spaces and punctuation, which are not allowed in IRIs
        name = display_name(item)
        ri = DATA[slugify(name)]

        # RI
        # (subject, predicate, object triples)
        # every ROR facility is typed SingleSitedRI. ROR records carry no
        # hub/node or "no physical site" structure, so distributed/virtual RIs are
        # indistinguishable here; single-sited is the only type assertable
        # from ROR data. 
        g.add((ri, RDF.type, OWL.NamedIndividual))
        g.add((ri, RDF.type, RIRPDM.SingleSitedRI))
        g.add((ri, RDFS.label, Literal(name, lang="en")))
        g.add((ri, RIRPDM.uniqueName, Literal(name)))
        g.add((ri, DCTERMS.source, Literal("ROR API")))
        g.add((ri, DCTERMS.identifier, Literal(item["id"])))  # ROR id -> used to fetch publications

        # website, falling back to the ROR record's own URL if none
        website = next((l["value"] for l in item["links"] if l["type"] == "website"), item["id"])
        g.add((ri, RIRPDM.accessPoint, Literal(website)))

        # country: create the Country individual once, then reuse it
        locations = item.get("locations") or []
        if locations:
            country_name = locations[0]["geonames_details"]["country_name"]
            if country_name not in countries:
                countries[country_name] = slugify(country_name)
                country = DATA[countries[country_name]]
                g.add((country, RDF.type, OWL.NamedIndividual))
                g.add((country, RDF.type, RIRPDM.Country))
                g.add((country, RDFS.label, Literal(country_name, lang="en")))
            g.add((ri, RIRPDM.hasParticipant, DATA[countries[country_name]]))

    return g


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=1, help="ROR result pages to fetch (20/page)")
    args = parser.parse_args()

    facilities = fetch_facilities(args.pages)
    build_graph(facilities).serialize(destination=str(OUT_FILE), format="turtle")
    print(f"Written {len(facilities)} facilities -> {OUT_FILE}")


if __name__ == "__main__":
    main()