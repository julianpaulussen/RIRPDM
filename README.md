# RIRPDM - Research Infrastructure and Research Publications Data Model

A semantically enriched data model for representation and reasoning about research infrastructure.

<p align="center">
  <img src="https://img.shields.io/badge/OWL_2-000000?style=for-the-badge&logoColor=white" alt="OWL 2"/>
  <img src="https://img.shields.io/badge/SPARQL-000000?style=for-the-badge&logoColor=white" alt="SPARQL"/>
  <img src="https://img.shields.io/badge/Python-000000?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
</p>

## Namespace

```
prefix rirpdm: <http://www.example.org/rirpdm#>
```

## Ontology documentation (Widoco)

Live at https://julianpaulussen.github.io/RIRPDM/

Auto-built and deployed to `gh-pages` on every push to `main` via `.github/workflows/docs.yml` via GitHub Actions.

## Sample data (ABox)

The ABox is **not committed** due to size and possible copyright issues. The repository ships only the code that retrieves it. Generate it yourself before loading the ontology into Protégé or GraphDB:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# edit sample numbers inside script to fetch more or less data
chmod +x ./scripts/build_data.sh
./scripts/build_data.sh 
```

## SPARQL endpoint

1. Open GraphDB Desktop
2. Create repository: ID `rirpdm`, ruleset `OWL2-RL (Optimized)`
3. Import -> Upload RDF files -> select `ontology/rirpdm.ttl` and the four `ontology/*sample-data*.ttl` files

Endpoint: `http://localhost:7200/repositories/rirpdm`


## Query script

Runs all CQs against the GraphDB endpoint and prints results.
GraphDB must be running with `rirpdm` repository loaded.

```bash
python3 scripts/query_endpoint.py
```
