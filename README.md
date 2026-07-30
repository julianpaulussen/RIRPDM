# RIRPDM - Research Infrastructure and Research Publications Data Model

<p align="center">
  <img src="https://img.shields.io/badge/OWL_2-000000?style=for-the-badge&logoColor=white" alt="OWL 2"/>
  <img src="https://img.shields.io/badge/SPARQL-000000?style=for-the-badge&logoColor=white" alt="SPARQL"/>
  <img src="https://img.shields.io/badge/Python-000000?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/VIVO-000000?style=for-the-badge&logoColor=white" alt="VIVO"/>
</p>

## Namespace

```
prefix rirpdm: <http://www.example.org/rirpdm#>
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

## Setup

ToDo: write an init script

Fetch `nfdicore.owl` before opening in Protégé:

```bash
curl -o ontology/nfdicore.owl https://raw.githubusercontent.com/ISE-FIZKarlsruhe/nfdicore/main/nfdicore.owl
```

## Ontology visualization

Open [WebVOWL](https://service.tib.eu/webvowl/) → Upload → select `ontology/rirpdm.ttl` to render the full schema as an interactive graph.

## Ontology documentation (Widoco)

Live spec: https://julianpaulussen.github.io/RIRPDM/

Widoco also serializes the ontology on every build — these are generated, not committed:

| Format | URL |
|--------|-----|
| RDF/XML | https://julianpaulussen.github.io/RIRPDM/rirpdm.owl |
| Turtle | https://julianpaulussen.github.io/RIRPDM/ontology.ttl |
| N-Triples | https://julianpaulussen.github.io/RIRPDM/ontology.nt |
| JSON-LD | https://julianpaulussen.github.io/RIRPDM/ontology.jsonld |

Auto-built and deployed to `gh-pages` on every push to `main` via `.github/workflows/docs.yml`. To generate locally:

```bash
wget -O widoco.jar https://github.com/dgarijo/Widoco/releases/download/v1.4.25/widoco-1.4.25-jar-with-dependencies_JDK-17.jar

java -jar widoco.jar -ontFile ontology/rirpdm.ttl -outFolder docs \
  -uniteSections -includeAnnotationProperties -getOntologyMetadata \
  -noPlaceHolderText -rewriteAll -webVowl
```
```bash
cd docs && python3 -m http.server 8000
```

## Sample data (ABox)

The ABox is **not committed** — the data belongs to its upstream providers, so this
repository ships only the code that retrieves it. Generate it yourself before loading
the ontology anywhere:

```bash
pip install -r requirements.txt
./scripts/build_data.sh                # defaults: 8 RIs, 5 works/RI, 5 grants/RI, 60 institutions
./scripts/build_data.sh 12 10 8 100    # larger sample
```

No credentials needed; all four APIs are public. Each step feeds the next through the
shared ROR id, so run the pipeline script rather than the fetch scripts individually.
The APIs are live, so every run produces different content.

This writes four files, each carrying a `dcterms:source` on every individual:

| File | Source | Holds |
|------|--------|-------|
| `ontology/rirpdm-meril-sample-data.ttl` | MERIL / CatRIS | research infrastructures (name, type, ROR id) |
| `ontology/rirpdm-openalex-sample-data.ttl` | OpenAlex (CC0) | publications, KPI measurements, affiliated institutions |
| `ontology/rirpdm-openaire-sample-data.ttl` | OpenAIRE | funding / grants |
| `ontology/rirpdm-ror-relationships-sample-data.ttl` | ROR (CC0) | parent organizations (`org:subOrganizationOf`) |

All four are gitignored. `ontology/rirpdm-full.ttl` is a thin wrapper that
`owl:imports` the ontology plus all four graphs — load that one for reasoning over
everything at once, but only after the files exist.

## Loading in Protégé

```bash
/path/to/protege/run.sh ontology/rirpdm.ttl
```

Run HermiT reasoner (Reasoner → Start Reasoner) to check consistency and compute inferred hierarchy.



## SPARQL endpoint

1. Open GraphDB Desktop
2. Create repository: ID `rirpdm`, ruleset `OWL2-RL (Optimized)`
3. Import → Upload RDF files → select `ontology/rirpdm.ttl` and the four `ontology/*sample-data*.ttl` files, format Turtle

Endpoint: `http://localhost:7200/repositories/rirpdm`

Load via curl:
```bash
curl -X POST http://localhost:7200/repositories/rirpdm/statements \
  -H "Content-Type: text/turtle" \
  --data-binary @ontology/rirpdm.ttl

for f in ontology/*sample-data*.ttl; do
  curl -X POST http://localhost:7200/repositories/rirpdm/statements \
    -H "Content-Type: text/turtle" \
    --data-binary @"$f"
done
```

## Competency questions

Standalone SPARQL query files are in `sparql/`.


## Query script

Runs all CQs against the GraphDB endpoint and prints results.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/query_endpoint.py
```

GraphDB must be running with `rirpdm` repository loaded.