"""Discover research infrastructures from the MERIL/CatRIS catalogue (semantics.gr).

For each RI we take its name/acronym/website/type, resolve the type code to one of
our RI subclasses, and match the name to a ROR id (via ROR's affiliation matcher)
so the downstream OpenAlex/OpenAIRE steps can join on it. RI IRIs are keyed on the
ROR id (ri_<rortail>). RIs without a confident ROR match are skipped -- they can't
be joined to publications or funding anyway.

Also emitted from MERIL: life-cycle phase (mapped onto the closed LifecyclePhase
enum), legal status, ESFRI status (as an ESFRILandmark/ESFRIProject type), a
MajorUpgrade proposal where MERIL reports one, and the coordinating/participating
countries -- grounding CQ01, CQ03, CQ04 and CQ05.

Usage:
    python3 scripts/fetch_data_meril.py                 # 8 RIs
    python3 scripts/fetch_data_meril.py --limit 15
"""
import argparse
import urllib.parse
import urllib.request
import json
import re
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.namespace import OWL, DCTERMS

OUT_FILE = Path(__file__).parent.parent / "ontology" / "rirpdm-meril-sample-data.ttl"
API_KEY = "14afd891-0f0c-4b32-b000-da00152d2481"  # public CatRIS key from the CatRIS D5.3 deliverable
SEM = "https://www.semantics.gr/authorities"
PROVIDERS_URL = f"{SEM}/vocabularies/CatRISMERILProvider/xml?apiKey={API_KEY}"
VOCAB_URL = SEM + "/vocabularies/{v}/xml?apiKey=" + API_KEY
ROR_MATCH = "https://api.ror.org/organizations?affiliation={q}"

RIRPDM = Namespace("http://www.example.org/rirpdm#")
DATA = Namespace("http://www.example.org/rirpdm/data#")
CATRIS = Namespace("https://www.semantics.gr/authorities/schemanamespaces/catris#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

# Map MERIL's controlled vocabularies onto our ontology

# MERIL provider type label -> our RI subclass
TYPE_CLASS = {"Single-sited": RIRPDM.SingleSitedRI,
              "Distributed": RIRPDM.DistributedRI,
              "Virtual": RIRPDM.VirtualRI}
# MERIL ESFRI status label
ESFRI_CLASS = {"RI is an ESFRI landmark": RIRPDM.ESFRILandmark,
               "RI is an ESFRI project": RIRPDM.ESFRIProject}
# MERIL lifecycle label -> our LifecyclePhase individual
# "Being Upgraded" is not a phase: the RI keeps operating, and the upgrade itself
# is emitted separately as a MajorUpgrade proposal (see build_graph).
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
    # controlled lists these fields reference by URI (type is inlined, these are not)
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
        # MERIL can classify one provider under several types (CLARIN is Virtual and
        # Distributed), so keep all of them -- VirtualRI is not disjoint with the others.
        pc = src.value(prov, CATRIS.providerClassification)
        ri_classes = set()
        for type_node in (src.objects(pc, CATRIS.type) if pc else []):
            label = src.value(type_node, SKOS.prefLabel)  # semantics.gr inlines the label
            if str(label) in TYPE_CLASS:
                ri_classes.add(TYPE_CLASS[str(label)])
        # Single-sited and Distributed are disjoint: a record claiming both is broken
        # source data that would make the merged ontology inconsistent (2 of 1750 do).
        if not ri_classes or {RIRPDM.SingleSitedRI, RIRPDM.DistributedRI} <= ri_classes:
            continue                                 # unknown/blank/contradictory -> skip

        ror = match_ror(str(acronym) if acronym else str(name))
        if not ror:
            continue                                 # no confident ROR -> can't join downstream

        ri = DATA["ri_" + ror_tail(ror)]
        g.add((ri, RDF.type, OWL.NamedIndividual))
        for ri_class in sorted(ri_classes):           # sorted -> stable output across runs
            g.add((ri, RDF.type, ri_class))
        g.add((ri, RDFS.label, Literal(str(name), lang="en")))
        g.add((ri, RIRPDM.uniqueName, Literal(str(name))))
        if website:
            g.add((ri, RIRPDM.accessPoint, Literal(str(website))))
        g.add((ri, DCTERMS.identifier, Literal(ror)))     # ROR url -> OpenAlex/OpenAIRE join key
        g.add((ri, DCTERMS.source, Literal("MERIL / semantics.gr")))

        # --- enrichment: fields ROR can't give (CQ01 phase, CQ03, CQ04, CQ05) ---
        life_label = lifecycle.get(str(src.value(prov, CATRIS.lifeCycleStatus))) or ""
        phase_ind = PHASE_IND.get(life_label)
        if phase_ind:
            g.add((ri, RIRPDM.isInPhase, phase_ind))  # map onto the closed enum, don't mint

        if life_label == "Being Upgraded":            # the upgrade is a Proposal about the RI
            upgrade = DATA["upgrade_" + ror_tail(ror)]
            g.add((upgrade, RDF.type, OWL.NamedIndividual))
            g.add((upgrade, RDF.type, RIRPDM.MajorUpgrade))
            g.add((upgrade, RDFS.label, Literal(f"Major upgrade of {name}", lang="en")))
            g.add((upgrade, RIRPDM.upgradesRI, ri))

        legal_label = legal.get(str(src.value(prov, CATRIS.legalStatus)))
        if legal_label and legal_label != "Other":
            g.add((ri, RIRPDM.legalStatus, Literal(legal_label)))

        esfri_class = ESFRI_CLASS.get(esfri.get(str(src.value(prov, CATRIS.esfri))) or "")
        if esfri_class:                          # orthogonal axis; safe alongside the site-structure type
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
    parser.add_argument("--limit", type=int, default=8, help="RIs to emit (matched to ROR)")
    args = parser.parse_args()
    build_graph(args.limit).serialize(destination=str(OUT_FILE), format="turtle")
    print(f"Written MERIL RIs -> {OUT_FILE}")


if __name__ == "__main__":
    main()
