"""Discover research infrastructures from the MERIL/CatRIS catalogue (semantics.gr).

Usage:
    python3 scripts/fetch_data_meril.py # 8 RIs default
    python3 scripts/fetch_data_meril.py --limit 15
"""
import argparse
import sys
import urllib.parse
import urllib.request
import json
import re
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.namespace import OWL, DCTERMS

OUT_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-meril-sample-data.ttl"
API_KEY = "14afd891-0f0c-4b32-b000-da00152d2481" # api key from document
SEM = "https://www.semantics.gr/authorities"
PROVIDERS_URL = f"{SEM}/vocabularies/CatRISMERILProvider/xml?apiKey={API_KEY}"
VOCAB_URL = SEM + "/vocabularies/{v}/xml?apiKey=" + API_KEY
ROR_MATCH = "https://api.ror.org/organizations?affiliation={q}"

RIRPDM = Namespace("http://www.example.org/rirpdm#")
DATA = Namespace("http://www.example.org/rirpdm/data#")
CATRIS = Namespace("https://www.semantics.gr/authorities/schemanamespaces/catris#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

# Map MERILs vocabularies onto our ontology

# MERIL provider type label -> our RI subclass
TYPE_CLASS = {"Single-sited": RIRPDM.SingleSitedRI,
              "Distributed": RIRPDM.DistributedRI,
              "Virtual": RIRPDM.VirtualRI}
# MERIL ESFRI status label
ESFRI_CLASS = {"RI is an ESFRI landmark": RIRPDM.ESFRILandmark,
               "RI is an ESFRI project": RIRPDM.ESFRIProject}
# MERIL lifecycle label -> our LifecyclePhase individual
# "Being Upgraded" is not a phase
PHASE_IND = {"Operational": RIRPDM.Operation,
             "Under Construction": RIRPDM.Implementation,
             "Being Upgraded": RIRPDM.Operation}


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", text)


def get(url: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        return resp.read()


def resolve_vocab(name: str) -> dict[str, str]:
    """Load a semantics.gr controlled list, return {concept-URI: prefLabel}."""
    g = Graph()
    g.parse(data=get(VOCAB_URL.format(v=name)), format="xml")
    return {str(s): str(o) for s, o in g.subject_objects(SKOS.prefLabel)}


def match_ror(name: str) -> str | None:
    """Return the ROR id ROR's affiliation matcher is confident about, else None."""
    if not name:
        return None
    data = json.loads(get(ROR_MATCH.format(q=urllib.parse.quote(name))))
    for item in data.get("items", []):
        if item.get("chosen"):
            return item["organization"]["id"]
    return None


def ror_tail(ror_url: str) -> str:
    return ror_url.rstrip("/").rsplit("/", 1)[-1]


def build_graph(limit: int) -> Graph:
    src = Graph()
    src.parse(data=get(PROVIDERS_URL), format="xml")
    # controlled lists these fields reference by URI 
    lifecycle = resolve_vocab("CatRISProviderLifeCycleStatus")
    legal = resolve_vocab("CatRISProviderLegalStatus")
    esfri = resolve_vocab("CatRISProviderESFRI")
    location = resolve_vocab("CatRISLocation")

    g = Graph()
    g.bind("rirpdm", RIRPDM)
    g.bind("data", DATA)
    ontology = URIRef("http://www.example.org/rirpdm/data-meril")
    g.add((ontology, RDF.type, OWL.Ontology))
    g.add((ontology, RDFS.label, Literal("RIRPDM MERIL-sourced RI data", lang="en")))
    g.add((ontology, OWL.imports, URIRef("http://www.example.org/rirpdm")))

    countries: dict[str, URIRef] = {}  # country name -> individual, emitted once
    kept = 0

    # For each MERIL RI, emit an individual with its type, name, ROR id, ...
    for prov in src.subjects(RDF.type, CATRIS.Provider):
        if kept >= limit:
            break
        name = src.value(prov, CATRIS.providerFullName)
        acronym = src.value(prov, CATRIS.providerAcronym)
        website = src.value(prov, CATRIS.providerWebsite)
        # MERIL can classify one provider under several types 
        # (CLARIN is Virtual and Distributed), so keep all of them.
        pc = src.value(prov, CATRIS.providerClassification)
        ri_classes = set()
        for type_node in (src.objects(pc, CATRIS.type) if pc else []):
            label = src.value(type_node, SKOS.prefLabel)  # semantics.gr inlines the label
            if str(label) in TYPE_CLASS:
                ri_classes.add(TYPE_CLASS[str(label)])
        # Single-sited and Distributed are disjoint
        if not ri_classes or {RIRPDM.SingleSitedRI, RIRPDM.DistributedRI} <= ri_classes:
            continue                                 

        ror = match_ror(str(acronym) if acronym else str(name))
        if not ror:
            continue                                

        ri = DATA["ri_" + ror_tail(ror)]
        g.add((ri, RDF.type, OWL.NamedIndividual))
        for ri_class in sorted(ri_classes):           
            g.add((ri, RDF.type, ri_class))
        g.add((ri, RDFS.label, Literal(str(name), lang="en")))
        g.add((ri, RIRPDM.uniqueName, Literal(str(name))))
        if website:
            g.add((ri, RIRPDM.accessPoint, Literal(str(website))))
        # here is the ror join key
        g.add((ri, DCTERMS.identifier, Literal(ror)))     
        g.add((ri, DCTERMS.source, Literal("MERIL / semantics.gr")))

        life_label = lifecycle.get(str(src.value(prov, CATRIS.lifeCycleStatus))) or ""
        phase_ind = PHASE_IND.get(life_label)
        if phase_ind:
            g.add((ri, RIRPDM.isInPhase, phase_ind))  # map onto the closed enum, don't mint
        elif life_label:
            print(f" unmapped lifeCycleStatus {life_label!r} for {name}", file=sys.stderr)

        if life_label == "Being Upgraded":         
            upgrade = DATA["upgrade_" + ror_tail(ror)]
            g.add((upgrade, RDF.type, OWL.NamedIndividual))
            g.add((upgrade, RDF.type, RIRPDM.MajorUpgrade))
            g.add((upgrade, RDFS.label, Literal(f"Major upgrade of {name}", lang="en")))
            g.add((upgrade, RIRPDM.upgradesRI, ri))

        legal_label = legal.get(str(src.value(prov, CATRIS.legalStatus)))
        if legal_label and legal_label != "Other":
            g.add((ri, RIRPDM.legalStatus, Literal(legal_label)))

        esfri_class = ESFRI_CLASS.get(esfri.get(str(src.value(prov, CATRIS.esfri))) or "")
        if esfri_class:                         
            g.add((ri, RDF.type, esfri_class))

        loc = src.value(prov, CATRIS.locationInfo)
        if loc:
            country_uris = [src.value(loc, CATRIS.coordinatingCountry)] + \
                           list(src.objects(loc, CATRIS.participatingCountry))
            for cu in country_uris:
                cname = location.get(str(cu)) if cu else None
                if not cname:
                    continue
                if cname not in countries:
                    countries[cname] = DATA["country_" + slug(cname)]
                    g.add((countries[cname], RDF.type, OWL.NamedIndividual))
                    g.add((countries[cname], RDF.type, RIRPDM.Country))
                    g.add((countries[cname], RDFS.label, Literal(cname, lang="en")))
                g.add((ri, RIRPDM.hasParticipant, countries[cname]))

        kept += 1

    return g


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=15, help="RIs to emit (matched to ROR)")
    args = parser.parse_args()
    build_graph(args.limit).serialize(destination=str(OUT_FILE), format="turtle")
    print(f"Written MERIL RIs -> {OUT_FILE}")


if __name__ == "__main__":
    main()
