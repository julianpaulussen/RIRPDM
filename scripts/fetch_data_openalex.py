"""Fetch publications from OpenAlex for RIs already emitted by fetch_data_ror.py.

Reads the ROR sample data, and for each RIs ROR id queries OpenAlex works
filtered by that institution. Each work becomes a rirpdm:ScientificPublication
linked back to the RI via rirpdm:isOutputOf.

Usage:
    python3 scripts/fetch_data_openalex.py                 # 5 works per RI
    python3 scripts/fetch_data_openalex.py --per-page 10   # 10 works per RI
"""

import argparse
import itertools
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.namespace import OWL, DCTERMS, XSD

ROR_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-meril-sample-data.ttl"
OUT_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-openalex-sample-data.ttl"
OPENALEX_URL = "https://api.openalex.org/works?filter=institutions.ror:{ror}&per-page={n}"

RIRPDM = Namespace("http://www.example.org/rirpdm#")
DATA = Namespace("http://www.example.org/rirpdm/data#")
FABIO = Namespace("http://purl.org/spar/fabio/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
CITO = Namespace("http://purl.org/spar/cito/")

TOP_CITED_FRACTION = 0.10  # ESFRI KPI: top 10% most-cited


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


def ror_tail(ror_url: str) -> str:
    return ror_url.rstrip("/").rsplit("/", 1)[-1]


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
    g.bind("cito", CITO)

    # ontology header: this data file imports the RIRPDM ontology it uses
    ontology = URIRef("http://www.example.org/rirpdm/data-openalex")
    g.add((ontology, RDF.type, OWL.Ontology))
    g.add((ontology, RDFS.label, Literal("RIRPDM OpenAlex-sourced sample data", lang="en")))
    g.add((ontology, OWL.imports, URIRef("http://www.example.org/rirpdm")))

    researchers: set[str] = set()  # slug -> emit each author once
    institutions: set[str] = set()  # ror -> emit each ResearchInstitution once
    # (ri, year) -> publications, to build one NumberOfPublications KPI measurement each
    by_ri_year: dict[tuple[URIRef, int], list[URIRef]] = {}
    by_ri: dict[URIRef, list[URIRef]] = {}       # ri -> all its publications (top-cited KPI)
    citations: dict[URIRef, int] = {}            # pub -> cited_by_count, for ranking
    refs: list[tuple[URIRef, list[str]]] = []    # (pub, referenced OpenAlex ids), resolved after
    emitted: set[str] = set()                    # OpenAlex ids we actually emitted, to close cito:cites

    for ri, ror in ris:
        for work in fetch_works(ror, per_page):
            oa_id = openalex_id(work["id"])
            pub = DATA["pub_" + oa_id]
            emitted.add(oa_id)

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
            by_ri.setdefault(ri, []).append(pub)

            # citation data: count for ranking, references for the cito:cites graph
            citations[pub] = work.get("cited_by_count", 0)
            refs.append((pub, [openalex_id(w) for w in work.get("referenced_works", [])]))

            # for each authorship in the work, create a researcher individual and link it to the publication
            work_institutions: set[URIRef] = set()  # co-affiliated on this work -> collaboratesWith
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

                # author's institutions -> ResearchInstitution agents involved in this RI's output (CQ11)
                for inst in authorship.get("institutions", []):
                    ror = inst.get("ror")
                    name_inst = inst.get("display_name")
                    if not ror or not name_inst:
                        continue
                    institution = DATA["inst_" + ror_tail(ror)]
                    if ror not in institutions:
                        institutions.add(ror)
                        g.add((institution, RDF.type, OWL.NamedIndividual))
                        g.add((institution, RDF.type, RIRPDM.ResearchInstitution))
                        g.add((institution, RDFS.label, Literal(name_inst, lang="en")))
                    g.add((ri, RIRPDM.involvesAgent, institution))
                    work_institutions.add(institution)

            # institutions that co-authored this work collaborate with each other (CQ11, CQ22)
            for a, b in itertools.combinations(work_institutions, 2):
                g.add((a, RIRPDM.collaboratesWith, b))  # symmetric -> reasoner infers b->a

    # cito:cites, but only between publications we actually emitted (closed graph)
    for pub, targets in refs:
        for t in targets:
            if t in emitted:
                g.add((pub, CITO.cites, DATA["pub_" + t]))

    # one NumberOfPublications KPI measurement per RI per year, counting the pubs
    for (ri, year), pubs in by_ri_year.items():
        slug = str(ri).rsplit("#", 1)[-1]
        m = DATA[f"kpim_{slug}_pubs_{year}"]
        g.add((m, RDF.type, OWL.NamedIndividual))
        g.add((m, RDF.type, RIRPDM.KPIMeasurement))
        g.add((m, RIRPDM.measuresKPI, RIRPDM.NumberOfPublications))
        g.add((m, RIRPDM.measurementYear, Literal(year, datatype=XSD.gYear)))
        g.add((m, RIRPDM.numericValue, Literal(len(pubs), datatype=XSD.decimal)))
        g.add((ri, RIRPDM.hasKPIMeasurement, m))
        for pub in pubs:
            g.add((m, RIRPDM.derivedFromOutput, pub))

    add_top_cited_kpi(g, by_ri, citations)
    return g


def add_top_cited_kpi(g: Graph, by_ri: dict[URIRef, list[URIRef]], citations: dict[URIRef, int]) -> None:
    """PercentageOfTopCitedPublications per RI: share of its pubs in the top-cited set."""
    
    if not citations:
        return
    ranked = sorted(citations.values(), reverse=True)
    # cutoff_idx is the index of the last pub that is in the top-cited fraction
    # if there are fewer pubs than the fraction, we take all of them
    cutoff_idx = max(0, int(TOP_CITED_FRACTION * len(ranked)) - 1)
    threshold = ranked[cutoff_idx] # pubs at/above this count are "top-cited"

    # for each RI, find its top-cited pubs and create a KPI measurement for the percentage
    for ri, pubs in by_ri.items():
        top = [p for p in pubs if citations.get(p, 0) >= threshold]
        slug = str(ri).rsplit("#", 1)[-1]
        m = DATA[f"kpim_{slug}_topcited"]
        g.add((m, RDF.type, OWL.NamedIndividual))
        g.add((m, RDF.type, RIRPDM.KPIMeasurement))
        g.add((m, RIRPDM.measuresKPI, RIRPDM.PercentageOfTopCitedPublications))
        g.add((m, RIRPDM.numericValue,
               Literal(round(100 * len(top) / len(pubs), 1), datatype=XSD.decimal)))
        g.add((ri, RIRPDM.hasKPIMeasurement, m))
        for p in top:
            g.add((m, RIRPDM.derivedFromOutput, p))


def verify_counts(g: Graph) -> None:
    """CQ21 invariant: a NumberOfPublications measurement's numericValue equals its
    derivedFromOutput count."""
    for m in g.subjects(RIRPDM.measuresKPI, RIRPDM.NumberOfPublications):
        val = next(g.objects(m, RIRPDM.numericValue))
        linked = len(list(g.objects(m, RIRPDM.derivedFromOutput)))
        assert float(str(val)) == linked, f"{m}: numericValue {val} != {linked} linked outputs"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-page", type=int, default=10, help="OpenAlex works to fetch per RI")
    args = parser.parse_args()

    ris = read_ris()
    g = build_graph(ris, args.per_page)
    verify_counts(g)  # CQ21 invariant holds before we write
    
    # rewrite file each run you run the script
    g.serialize(destination=str(OUT_FILE), format="turtle")
    print(f"Written publications for {len(ris)} RIs -> {OUT_FILE}")


if __name__ == "__main__":
    main()
