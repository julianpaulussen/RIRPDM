#!/usr/bin/env bash

# Rebuild the sample-data ABox from the public APIs.
# Order matters -- each step feeds the next through the shared ROR id:
# 1. MERIL discovers real RIs (name, type, ROR id) from the CatRIS catalogue.
# 2. OpenAlex reads those RIs and backfills their publications, KPI measurements
#    and author-affiliated institutions (+ their collaboratesWith edges).
# 3. OpenAIRE reads those RIs and backfills their funding.
# 4. ROR resolves each institution's parent org (org:subOrganizationOf), if any.

# Usage:
#   ./scripts/build_data.sh              # 8 RIs, 5 works/RI, 5 grants/RI, 60 insts (defaults)
#   ./scripts/build_data.sh 12 10 8 100  # 12 RIs, 10 works/RI, 8 grants/RI, 100 insts

# Stop the pipeline if any step fails (so later steps never run on stale data):
# -e exit on error, -u exit on unset variable, -o pipefail exit if any pipe stage fails
set -euo pipefail

# Change working directory to the project root
cd "$(dirname "$0")/.."

python3 scripts/fetch_data_meril.py --limit "${1:-8}"
python3 scripts/fetch_data_openalex.py --per-page "${2:-5}"
python3 scripts/fetch_data_openaire.py --projects "${3:-5}"
python3 scripts/fetch_data_ror_relationships.py --limit "${4:-60}"
echo "Sample data rebuilt."
