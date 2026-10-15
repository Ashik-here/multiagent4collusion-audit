#!/usr/bin/env bash
# Gets everything the checks need, at the exact versions I looked at.
# Repos are only cloned, nothing is installed or run.
# Usage: bash scripts/get_sources.sh   (puts it all in ./sources, which is gitignored)
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p sources
cd sources

clone_at() {  # clone_at <url> <folder> <commit> [extra git clone options]
    local url=$1 dir=$2 commit=$3
    shift 3
    if [ ! -d "$dir" ]; then
        git clone -q "$@" "$url" "$dir"
    fi
    git -C "$dir" -c advice.detachedHead=false checkout -q "$commit"
    echo "$dir at $(git -C "$dir" rev-parse HEAD)"
}

# The code released with the paper.
clone_at https://github.com/renqibing/MultiAgent4Collusion.git MultiAgent4Collusion \
    b6daeff24883a4c253858c4dab3261383f888243

# CoAID, the COVID-19 misinformation dataset the posts come from.
clone_at https://github.com/cuilimeng/CoAID.git CoAID \
    d238224346781255e1e7e6ed8bc410c2b2e6329e

# OASIS, the simulator the code builds on. It is large, so only the history is cloned;
# hash_check.sh reads the files it needs with `git show`.
if [ ! -d oasis ]; then
    git clone -q --filter=blob:none --no-checkout https://github.com/camel-ai/oasis.git oasis
fi
echo "oasis cloned (no checkout; files are read at specific commits)"

# FakeNewsNet's four dataset files, the source the paper names.
FNN=654361e1c8d5baa751baf1dac5032df621652280
mkdir -p fakenewsnet
for f in politifact_fake politifact_real gossipcop_fake gossipcop_real; do
    if [ ! -f "fakenewsnet/$f.csv" ]; then
        curl -sSfL -o "fakenewsnet/$f.csv" \
            "https://raw.githubusercontent.com/KaiDMML/FakeNewsNet/$FNN/dataset/$f.csv"
    fi
done
echo "fakenewsnet CSVs at $FNN"
