"""Fetch publications from OpenAlex for RIs already emitted by fetch_data_ror.py.

Reads the ROR sample data, and for each RIs ROR id queries OpenAlex works
filtered by that institution. Each work becomes a rirpdm:ScientificPublication
linked back to the RI via rirpdm:isOutputOf.

Usage:
    python3 scripts/fetch_data_openalex.py                 # 5 works per RI
    python3 scripts/fetch_data_openalex.py --per-page 10   # 10 works per RI
"""

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.namespace import OWL, DCTERMS, XSD

ROR_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-ror-sample-data.ttl"
OUT_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-openalex-sample-data.ttl"
OPENALEX_URL = "https://api.openalex.org/works?filter=institutions.ror:{ror}&per-page={n}"

RIRPDM = Namespace("http://www.example.org/rirpdm#")
DATA = Namespace("http://www.example.org/rirpdm/data#")
FABIO = Namespace("http://purl.org/spar/fabio/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")


def slugify(name: str) -> str:
    """Turn a name into a safe IRI fragment: 'Jane Q. Doe' -> 'JaneQDoe'."""
    return re.sub(r"[^A-Za-z0-9]", "", name)


def bare_doi(doi_url: str | None) -> str | None:
    """OpenAlex gives 'https://doi.org/10.1/x'; keep the bare '10.1/x' for hasDOI."""
    if not doi_url:
        return None
    return doi_url.replace("https://doi.org/", "")


def openalex_id(work_id: str) -> str:
    """OpenAlex id is a URL 'https://openalex.org/W123'; keep the 'W123' tail."""
    return work_id.rsplit("/", 1)[-1]


def read_ris() -> list[tuple[URIRef, str]]:
    """Load the ROR sample data, return (RI individual IRI, ROR id) pairs."""
    g = Graph()
    g.parse(ROR_FILE, format="turtle")
    ris = []
    for ri, _, ror in g.triples((None, DCTERMS.identifier, None)):
        if str(ror).startswith("https://ror.org/"):
            ris.append((ri, str(ror)))
    return ris


def fetch_works(ror: str, per_page: int) -> list[dict]:
    """Query OpenAlex for works by the given ROR id, return the JSON results."""
    url = OPENALEX_URL.format(ror=urllib.parse.quote(ror, safe=""), n=per_page)
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)["results"]


def build_graph(ris: list[tuple[URIRef, str]], per_page: int) -> Graph:
    g = Graph()
    # bind the namespaces 
    g.bind("rirpdm", RIRPDM)
    g.bind("data", DATA)
    g.bind("fabio", FABIO)
    g.bind("foaf", FOAF)

    # ontology header: this data file imports the RIRPDM ontology it uses
    ontology = URIRef("http://www.example.org/rirpdm/data-openalex")
    g.add((ontology, RDF.type, OWL.Ontology))
    g.add((ontology, RDFS.label, Literal("RIRPDM OpenAlex-sourced sample data", lang="en")))
    g.add((ontology, OWL.imports, URIRef("http://www.example.org/rirpdm")))

    researchers: set[str] = set()  # slug -> emit each author once
    # (ri, year) -> publications, to build one NumberOfPublications KPI measurement each
    by_ri_year: dict[tuple[URIRef, int], list[URIRef]] = {}

    for ri, ror in ris:
        for work in fetch_works(ror, per_page):
            pub = DATA["pub_" + openalex_id(work["id"])]

            # subject, predicate, object
            # Add the publication individual, its type, and its properties
            g.add((pub, RDF.type, OWL.NamedIndividual))
            g.add((pub, RDF.type, RIRPDM.ScientificPublication))
            if work.get("title"):
                g.add((pub, RDFS.label, Literal(work["title"], lang="en")))
                g.add((pub, DCTERMS.title, Literal(work["title"])))
            doi = bare_doi(work.get("doi"))
            if doi:  
                g.add((pub, FABIO.hasDOI, Literal(doi)))
            year = work.get("publication_year")
            if year:
                g.add((pub, DCTERMS.created, Literal(year, datatype=XSD.gYear)))
                by_ri_year.setdefault((ri, year), []).append(pub)
            g.add((pub, RIRPDM.providesOpenAccess,
                   Literal(bool(work.get("open_access", {}).get("is_oa", False)), datatype=XSD.boolean)))
            g.add((pub, DCTERMS.source, Literal("OpenAlex")))

            # the bridge: this publication was produced by the queried RI
            g.add((pub, RIRPDM.isOutputOf, ri))

            # for each authorship in the work, create a researcher individual and link it to the publication
            for authorship in work.get("authorships", []):
                name = authorship.get("author", {}).get("display_name")
                if not name:
                    continue
                person = DATA["person_" + slugify(name)]
                if name not in researchers:
                    researchers.add(name)
                    g.add((person, RDF.type, OWL.NamedIndividual))
                    g.add((person, RDF.type, RIRPDM.Researcher))
                    g.add((person, RDFS.label, Literal(name, lang="en")))
                g.add((pub, RIRPDM.hasAuthor, person))  # inverseOf authorOf -> feeds CQ19 chain

    # one NumberOfPublications KPI measurement per RI per year, counting the pubs
    for (ri, year), pubs in by_ri_year.items():
        slug = str(ri).rsplit("#", 1)[-1]
        m = DATA[f"kpim_{slug}_{year}"]
        g.add((m, RDF.type, OWL.NamedIndividual))
        g.add((m, RDF.type, RIRPDM.KPIMeasurement))
        g.add((m, RIRPDM.measuresKPI, RIRPDM.NumberOfPublications))
        g.add((m, RIRPDM.measurementYear, Literal(year, datatype=XSD.gYear)))
        g.add((m, RIRPDM.numericValue, Literal(len(pubs), datatype=XSD.decimal)))
        g.add((ri, RIRPDM.hasKPIMeasurement, m))
        for pub in pubs:
            g.add((m, RIRPDM.derivedFromOutput, pub))

    return g


def verify_counts(g: Graph) -> None:
    """CQ21 invariant: each measurement's numericValue equals its derivedFromOutput count."""
    for m, _, val in g.triples((None, RIRPDM.numericValue, None)):
        linked = len(list(g.objects(m, RIRPDM.derivedFromOutput)))
        assert float(str(val)) == linked, f"{m}: numericValue {val} != {linked} linked outputs"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-page", type=int, default=5, help="OpenAlex works to fetch per RI")
    args = parser.parse_args()

    ris = read_ris()
    g = build_graph(ris, args.per_page)
    verify_counts(g)  # CQ21 invariant holds before we write
    
    # rewrite file each run you run the script
    g.serialize(destination=str(OUT_FILE), format="turtle")
    print(f"Written publications for {len(ris)} RIs -> {OUT_FILE}")


if __name__ == "__main__":
    main()
