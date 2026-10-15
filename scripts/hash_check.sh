#!/usr/bin/env bash
# Compares files byte for byte using SHA-256. Hashes are taken from git (`git show`) so Windows
# line-ending conversion doesn't mess them up.
# Usage: bash scripts/hash_check.sh   (run scripts/get_sources.sh first)
set -euo pipefail

cd "$(dirname "$0")/../sources"
REN=b6daeff24883a4c253858c4dab3261383f888243
COAID=d238224346781255e1e7e6ed8bc410c2b2e6329e
OASIS_EMALL=98da5c2137db785af45affbe216b9acd78ca31aa   # OASIS, 5 Dec 2024
OASIS_PYPROJECT=093c0526fcf3c2f727c4745c9c4f5a27658b4c83
OASIS_LOCK=5504f8442ab7e2f463ca2c6385dd33006c0bc6b1

sha() { if command -v sha256sum >/dev/null; then sha256sum; else shasum -a 256; fi | cut -c1-64; }
ren()   { git -C MultiAgent4Collusion show "$REN:$1" | sha; }
oasis() { git -C oasis show "$1:$2" | sha; }
same()  { [ "$1" = "$2" ] && echo "identical" || echo "DIFFERENT"; }

echo "== 1. E-commerce files: MultiAgent4Collusion vs OASIS demo at ${OASIS_EMALL:0:7}"
for p in data/emall/product.json data/reddit/user_data_36.json \
         scripts/reddit_emall_demo/emall_simulation.py scripts/reddit_emall_demo/emall.yaml \
         scripts/reddit_emall_demo/action_space_prompt.txt oasis/social_platform/schema/product.sql; do
    a=$(ren "$p"); b=$(oasis "$OASIS_EMALL" "$p")
    echo "$(same "$a" "$b")  $a  $p"
done

echo
echo "== 2. Dependency files: MultiAgent4Collusion vs OASIS"
a=$(ren pyproject.toml); b=$(oasis "$OASIS_PYPROJECT" pyproject.toml)
echo "$(same "$a" "$b")  $a  pyproject.toml (OASIS ${OASIS_PYPROJECT:0:7})"
a=$(ren poetry.lock); b=$(oasis "$OASIS_LOCK" poetry.lock)
echo "$(same "$a" "$b")  $a  poetry.lock (OASIS ${OASIS_LOCK:0:7})"

echo
echo "== 3. CoAID news files: copy in MultiAgent4Collusion vs official CoAID at ${COAID:0:7}"
for d in 05-01-2020 07-01-2020 09-01-2020 11-01-2020; do
    for f in NewsFakeCOVID-19.csv NewsRealCOVID-19.csv; do
        a=$(ren "data/tweets/CoAID/$d/$f"); b=$(git -C CoAID show "$COAID:$d/$f" | sha)
        echo "$(same "$a" "$b")  $a  $d/$f"
    done
done

echo
echo "== 4. Released agent files that are byte-identical copies of each other"
git -C MultiAgent4Collusion ls-tree -r --name-only "$REN" data/our_twitter_sim | grep '\.csv$' |
while read -r f; do echo "$(ren "$f")  ${f#data/our_twitter_sim/}"; done | sort > /tmp/agent_file_hashes.$$
cut -c1-64 /tmp/agent_file_hashes.$$ | uniq -d | while read -r h; do
    echo "-- group ${h:0:12}"
    grep "^$h" /tmp/agent_file_hashes.$$ | cut -c67- | sed 's/^/   /'
done
echo "(all $(wc -l < /tmp/agent_file_hashes.$$) agent files hashed; files not listed are unique)"
rm -f /tmp/agent_file_hashes.$$
