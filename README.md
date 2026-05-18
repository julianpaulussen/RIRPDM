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

## SPARQL endpoint

Load into GraphDB after download:

```bash
curl -X POST http://localhost:7200/repositories/rirpdo/statements \
  -H "Content-Type: text/turtle" \
  --data-binary @rirpdo.ttl
```

Endpoint: `http://localhost:7200/repositories/rirpdo`