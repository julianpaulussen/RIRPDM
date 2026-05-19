# RIRPDO — Research Infrastructure and Research Publications Data Ontology

OWL 2 ontology for knowledge representation and reasoning over scientific research infrastructure and publications.

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

RIRPDO declares equivalence with VIVO terms, enabling interoperability with VIVO-based systems:

| RIRPDO | VIVO |
|--------|------|
| `rirpdo:Researcher` | `vivo:Researcher` |
| `rirpdo:ResearchGroup` | `vivo:ResearchGroup` |
| `rirpdo:Laboratory` | `vivo:Laboratory` |
| `rirpdo:Project` | `vivo:Project` |
| `rirpdo:hasAuthor` | `vivo:hasAuthor` |
| `rirpdo:affiliatedWith` | `vivo:affiliatedWith` |
| `rirpdo:fundedBy` | `vivo:fundedBy` |
| `rirpdo:memberOf` | `vivo:memberOf` |

Querying with VIVO terms returns results inferred from RIRPDO data — no extra triples needed.

## Setup

Fetch `nfdicore.owl` before opening in Protégé:

```bash
curl -o nfdicore.owl https://raw.githubusercontent.com/ISE-FIZKarlsruhe/nfdicore/main/nfdicore.owl
```

## Loading in Protégé

```bash
/path/to/protege/run.sh rirpdo.ttl
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
3. Import → Upload RDF files → select `rirpdo.ttl`, format Turtle

Endpoint: `http://localhost:7200/repositories/rirpdo`

Load via curl:
```bash
curl -X POST http://localhost:7200/repositories/rirpdo/statements \
  -H "Content-Type: text/turtle" \
  --data-binary @rirpdo.ttl
```

## Competency questions

See `competency-questions.md` for all 5 CQs with SPARQL translations.

| CQ | Question |
|----|----------|
| CQ01 | Which researchers at institution X published on topic Y? |
| CQ02 | Which projects use which research infrastructure? |
| CQ03 | Which publications share a topic with a given publication? |
| CQ04 | Which datasets were produced by each project and via which infrastructure? |
| CQ05 | Which researchers have co-authored a publication? |
| CQ06 | Which research topic has the most publications? |
| CQ07 | Which institution hosts the most researchers? |

## Query script

Runs all 5 CQs against the GraphDB endpoint and prints results.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/query_endpoint.py
```

GraphDB must be running with `rirpdo` repository loaded.