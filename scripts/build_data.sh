#!/usr/bin/env bash

# Rebuild the sample-data ABox from the public APIs.
# Order matters: 
# 1. ROR is queried first: Output are the RI keys used to query OpenAlex.
# 2. OpenAlex is queried second: Output is the publications for the RIs.

# Usage:
#   ./scripts/build_data.sh           # 1 ROR page, 5 works/RI (defaults)
#   ./scripts/build_data.sh 3 10      # 3 ROR pages, 10 works/RI

# Stop before OpenAlex if the ROR fetch fails:
# -e is "exit on error"
# -u is "exit on unset variable"
# -o is "exit if any command in a pipeline fails"
set -euo pipefail

# Change working directory to the project root
cd "$(dirname "$0")/.."

# $1 -> first argument the user passed (e.g. 3)
# $2 -> second argument the user passed (e.g. 10)
# :- -> default operator, if ther user didn't pass an argument (use e.g. 1 or 5 instead)
python3 scripts/fetch_data_ror.py --pages "${1:-1}"
python3 scripts/fetch_data_openalex.py --per-page "${2:-5}"
echo "Sample data rebuilt."