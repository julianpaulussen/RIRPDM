# RIRPDO — Research Infrastructure and Research Publications Data Ontology

OWL 2 ontology for knowledge representation and reasoning over scientific research infrastructure and publications.

## Namespace

```
prefix rirpdo: <http://www.example.org/rirpdo#>
```

## Key ontology reuse

| Prefix | Source | Used for |
|--------|--------|----------|
| `foaf:` | FOAF | Persons, organizations |
| `bibo:` | BIBO | Publications, journals |
| `dc:` | Dublin Core | Metadata terms |
| `skos:` | SKOS | Research topics, keywords |
| `nfdicore:` | NFDIcore | Research infrastructure, projects, labs |

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

## Query script

Runs all 5 CQs against the GraphDB endpoint and prints results.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/query_endpoint.py
```

GraphDB must be running with `rirpdo` repository loaded.