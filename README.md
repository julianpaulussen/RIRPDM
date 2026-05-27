# RIRPDM - Research Infrastructure and Research Publications Data Model

<p align="center">
  <img src="https://img.shields.io/badge/OWL_2-000000?style=for-the-badge&logoColor=white" alt="OWL 2"/>
  <img src="https://img.shields.io/badge/SPARQL-000000?style=for-the-badge&logoColor=white" alt="SPARQL"/>
  <img src="https://img.shields.io/badge/Python-000000?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/VIVO-000000?style=for-the-badge&logoColor=white" alt="VIVO"/>
</p>

A semantically enriched data model for representation and reasoning about research infrastructure.

## Namespace

```
prefix rirpdo: <http://www.example.org/rirpdo#>
```

## Key ontology reuse

| Prefix | Source | Used for |
|--------|--------|----------|
| `foaf:` | FOAF | Persons, organizations (`owl:imports`) |
| `bibo:` | BIBO | Publications, journals (`owl:imports`) |
| `dc:` | Dublin Core | Metadata terms (`owl:imports`) |
| `skos:` | SKOS | Research topics, keywords (`owl:imports`) |
| `nfdicore:` | NFDIcore | Research infrastructure reference (`rdfs:seeAlso`) |
| `vivo:` | VIVO | Ontology alignment (`owl:equivalentClass` / `owl:equivalentProperty`) |

### VIVO alignment

RIRPDO uses `rdfs:seeAlso` to reference related VIVO terms as informational pointers. No `owl:equivalentClass` is declared — VIVO term semantics and IRI stability were not fully verified.

| RIRPDO | VIVO (rdfs:seeAlso) |
|--------|------|
| `rirpdo:Researcher` | `vivo:ResearcherRole` |
| `rirpdo:ResearchGroup` | `vivo:ResearchOrganization` |
| `rirpdo:Laboratory` | `vivo:Laboratory` |
| `rirpdo:Project` | `vivo:Project` |
| `rirpdo:hasAuthor` | `vivo:hasAuthor` |
| `rirpdo:affiliatedWith` | `vivo:affiliatedWith` |
| `rirpdo:fundedBy` | `vivo:fundedBy` |
| `rirpdo:memberOf` | `vivo:memberOf` |

## Repository structure

```
ontology/
  rirpdo.ttl              ← TBox (classes, properties, axioms)
  rirpdo-individuals.ttl  ← ABox (instance data)
  rirpdo.owl              ← RDF/XML export (generated)
  nfdicore.owl            ← external dependency (fetched separately)
sparql/
  cq00.rq                 ← test query (researchers + affiliations)
  cq01.rq                 ← CQ01 (infrastructure → publications bridge)
  cq02.rq                 ← CQ02 (infrastructure fragility / single point of failure)
  cq03.rq                 ← CQ03 (latent collaboration discovery)
  cq04.rq                 ← CQ04 (projects → infrastructure → funding)
scripts/
  query_endpoint.py       ← runs all CQs against GraphDB
  convert_to_owl.py       ← converts rirpdo.ttl → rirpdo.owl
  requirements.txt
docs/
  competency-questions.md
  NOTES.md
```

## Setup

Fetch `nfdicore.owl` before opening in Protégé:

```bash
curl -o ontology/nfdicore.owl https://raw.githubusercontent.com/ISE-FIZKarlsruhe/nfdicore/main/nfdicore.owl
```

## Ontology visualization

Open [WebVOWL](https://service.tib.eu/webvowl/) → Upload → select `ontology/rirpdo.ttl` to render the full schema as an interactive graph.

## Loading in Protégé

```bash
/path/to/protege/run.sh ontology/rirpdo.ttl
```

Run HermiT reasoner (Reasoner → Start Reasoner) to check consistency and compute inferred hierarchy.

## OWL axioms

| Axiom | Description |
|-------|-------------|
| `owl:inverseOf` | `authorOf` inferred as inverse of `hasAuthor` |
| `owl:disjointWith` | `Researcher`, `Publication`, `ResearchInfrastructure`, `ResearchTopic`, `Project`, `Institution` are mutually disjoint where applicable |
| `owl:minQualifiedCardinality` | Every `Project` must have ≥1 `hasParticipant` |

## SPARQL endpoint

1. Open GraphDB Desktop
2. Create repository: ID `rirpdo`, ruleset `OWL2-RL (Optimized)`
3. Import → Upload RDF files → select `ontology/rirpdo.ttl` and `ontology/rirpdo-individuals.ttl`, format Turtle

Endpoint: `http://localhost:7200/repositories/rirpdo`

Load via curl:
```bash
curl -X POST http://localhost:7200/repositories/rirpdo/statements \
  -H "Content-Type: text/turtle" \
  --data-binary @ontology/rirpdo.ttl

curl -X POST http://localhost:7200/repositories/rirpdo/statements \
  -H "Content-Type: text/turtle" \
  --data-binary @ontology/rirpdo-individuals.ttl
```

## Competency questions

Standalone SPARQL query files are in `sparql/`.

| CQ | Domain | Question |
|----|--------|----------|
| CQ00 | Test | List all researchers and their affiliations. |
| CQ01 | Both (bridge) | Which research infrastructures enabled the most publications on a given topic, and what institutions operated them? |
| CQ02 | Both (bridge) | Which research topics depend on a single research infrastructure for all their publication output? (fragility analysis) |
| CQ03 | Both (bridge) | Which pairs of institutions have co-used the same research infrastructure but never co-authored a publication? (latent collaboration) |
| CQ04 | Infrastructure | Which projects use research infrastructure, and who funds them? |

## Query script

Runs all CQs against the GraphDB endpoint and prints results.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/query_endpoint.py
```

GraphDB must be running with `rirpdo` repository loaded.