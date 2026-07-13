"""Backfill funding from OpenAIRE for the RIs MERIL discovered.

Prerequisite: fetch_data_meril.py has already written the RIs (with their ROR ids). 
Here, for each RI we look it up in OpenAIRE by its ROR, fetch the projects that fund it, and emit the funding chain in FRAPO terms:

RI --frapo:isFundedBy--> Grant --frapo:isAwardedBy--> FundingAgency
RI --rirpdm:isSupportedBy--> Grant --rirpdm:isSupportedBy--> {Programme, Agency}

RIs that OpenAIRE doesn't know (no org for the ROR) simply get no funding.

Usage:
    python3 scripts/fetch_data_openaire.py                 
    python3 scripts/fetch_data_openaire.py --projects 8
"""
import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.namespace import OWL, DCTERMS

MERIL_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-meril-sample-data.ttl"
OUT_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-openaire-sample-data.ttl"
ORG_URL = "https://api.openaire.eu/graph/v1/organizations?pid={ror}&pageSize=1"
PROJ_URL = "https://api.openaire.eu/graph/v1/projects?relOrganizationId={oid}&pageSize={n}"

RIRPDM = Namespace("http://www.example.org/rirpdm#")
DATA = Namespace("http://www.example.org/rirpdm/data#")
FRAPO = Namespace("http://purl.org/cerif/frapo/")


def slugify(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", text)


def ror_tail(ror_url: str) -> str:
    """'https://ror.org/01ggx4157' -> '01ggx4157'."""
    return ror_url.rstrip("/").rsplit("/", 1)[-1]


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)


def read_rors() -> list[str]:
    """Read the ROR ids MERIL emitted from its output ttl."""
    if not MERIL_FILE.exists():
        raise SystemExit(f"{MERIL_FILE} not found -- run fetch_data_meril.py first.")
    g = Graph()
    g.parse(MERIL_FILE, format="turtle")
    return sorted({str(o) for _, _, o in g.triples((None, DCTERMS.identifier, None))
                   if str(o).startswith("https://ror.org/")})


def org_id_for_ror(ror: str) -> str | None:
    """OpenAIRE organisation id for a ROR, or None if OpenAIRE doesn't know it."""
    data = get_json(ORG_URL.format(ror=urllib.parse.quote(ror, safe="")))
    results = data.get("results") or []
    return results[0]["id"] if results else None


def fetch_projects(org_id: str, n: int) -> list[dict]:
    data = get_json(PROJ_URL.format(oid=urllib.parse.quote(org_id, safe=""), n=n))
    return data.get("results") or []


def build_graph(rors: list[str], projects: int) -> Graph:
    g = Graph()
    g.bind("rirpdm", RIRPDM)
    g.bind("data", DATA)
    g.bind("frapo", FRAPO)

    ontology = URIRef("http://www.example.org/rirpdm/data-openaire")
    g.add((ontology, RDF.type, OWL.Ontology))
    g.add((ontology, RDFS.label, Literal("RIRPDM OpenAIRE-sourced funding data", lang="en")))
    g.add((ontology, OWL.imports, URIRef("http://www.example.org/rirpdm")))

    funders: set[str] = set()
    programmes: set[str] = set()

    # For each ROR, fetch the OpenAIRE org id
    for ror in rors:
        oid = org_id_for_ror(ror)
        if not oid:
            continue
        ri = DATA["ri_" + ror_tail(ror)] 
        # For each org id, fetch the projects that fund it
        for proj in fetch_projects(oid, projects):
            # code is the grant number
            code = proj.get("code")
            if not code:
                continue
            grant = DATA["grant_" + slugify(code)]
            g.add((grant, RDF.type, OWL.NamedIndividual))
            g.add((grant, RDF.type, FRAPO.Grant))
            g.add((grant, FRAPO.hasGrantNumber, Literal(code)))
            if proj.get("title"):
                g.add((grant, RDFS.label, Literal(proj["title"], lang="en")))
            g.add((grant, DCTERMS.source, Literal("OpenAIRE")))
            # RI <- grant: direct funding (CQ09) and the transitive support base (CQ10)
            g.add((ri, FRAPO.isFundedBy, grant))
            g.add((ri, RIRPDM.isSupportedBy, grant))

            # For each grant, emit the funder and programme (if any)
            for funding in proj.get("fundings") or []:
                fname = funding.get("name") or funding.get("shortName")
                if fname:
                    funder = DATA["funder_" + slugify(fname)]
                    if fname not in funders:
                        funders.add(fname)
                        g.add((funder, RDF.type, OWL.NamedIndividual))
                        g.add((funder, RDF.type, FRAPO.FundingAgency))
                        g.add((funder, RDFS.label, Literal(fname, lang="en")))
                    g.add((grant, FRAPO.isAwardedBy, funder))
                    g.add((grant, RIRPDM.isSupportedBy, funder))  # RI ->* funder (transitive)
                stream = (funding.get("fundingStream") or {}).get("description")
                if stream and stream != "null":
                    prog = DATA["programme_" + slugify(stream)]
                    if stream not in programmes:
                        programmes.add(stream)
                        g.add((prog, RDF.type, OWL.NamedIndividual))
                        g.add((prog, RDF.type, FRAPO.FundingProgramme))
                        g.add((prog, RDFS.label, Literal(stream, lang="en")))
                    g.add((grant, RIRPDM.isSupportedBy, prog))  # RI ->* programme (transitive)
    return g


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", type=int, default=5, help="projects (grants) per RI")
    args = parser.parse_args()

    rors = read_rors()
    build_graph(rors, args.projects).serialize(destination=str(OUT_FILE), format="turtle")
    print(f"Written funding for RIs matched in OpenAIRE -> {OUT_FILE}")


if __name__ == "__main__":
    main()
