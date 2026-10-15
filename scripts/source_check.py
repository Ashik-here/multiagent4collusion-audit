"""Checks where the starting posts in the released agent files come from.

The paper says FakeNewsNet. This looks up every post (exact string match) in the CoAID
NewsFake/NewsReal title columns and in the four FakeNewsNet CSVs, and also checks the two JSON
files the repo builds its posts from. Run scripts/get_sources.sh first.

Usage:  python scripts/source_check.py [sources folder]
"""
import ast
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")  # CoAID titles contain non-ASCII characters
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "sources")
REN = os.path.join(SRC, "MultiAgent4Collusion")
COAID = os.path.join(SRC, "CoAID")
FNN = os.path.join(SRC, "fakenewsnet")
DATES = ["05-01-2020", "07-01-2020", "09-01-2020", "11-01-2020"]

csv.field_size_limit(2**31 - 1)


def titles_with_location(path):
    """Map each title in a CSV to its first (file, line, row id)."""
    found = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        id_col = reader.fieldnames[0]
        for row in reader:
            t = row.get("title")
            if t and t not in found:
                found[t] = (os.path.relpath(path, SRC).replace("\\", "/"), reader.line_num, row[id_col])
    return found


def load_coaid(kind):
    out = {}
    for d in DATES:
        for t, loc in titles_with_location(os.path.join(COAID, d, f"News{kind}COVID-19.csv")).items():
            out.setdefault(t, loc)
    return out


def load_fnn():
    out = {}
    for name in ["politifact_fake", "politifact_real", "gossipcop_fake", "gossipcop_real"]:
        for t, loc in titles_with_location(os.path.join(FNN, f"{name}.csv")).items():
            out.setdefault(t, loc)
    return out


def agent_posts(path):
    """Yield (user_id, user_type, posts) for each row of an agent file."""
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            yield int(row["user_id"]), row["user_type"], ast.literal_eval(row["previous_tweets"])


def main():
    coaid_fake, coaid_real, fnn = load_coaid("Fake"), load_coaid("Real"), load_fnn()
    print(f"Titles loaded: CoAID fake {len(coaid_fake)}, CoAID real {len(coaid_real)}, FakeNewsNet {len(fnn)}")

    # The JSON files that agents_init.py samples posts from.
    for name, ref, label in [("fake_tweets_COVID.json", coaid_fake, "CoAID NewsFake titles"),
                             ("fake_tweets_politics.json", fnn, "FakeNewsNet titles")]:
        with open(os.path.join(REN, "data", "tweets", name), encoding="utf-8") as f:
            items = json.load(f)
        distinct = set(items)
        print(f"{name}: {len(items)} entries, {len(distinct)} distinct, "
              f"{sum(t in ref for t in distinct)} distinct entries found in {label}")

    print("\nStarting posts per agent file (malicious = user_type contains 'bad'):")
    print(f"{'file':78s} {'mal.posts':>9s} {'CoAID':>6s} {'FNN':>5s} {'neither':>7s} | {'ben.posts':>9s} {'CoAID-real':>10s}")
    data = os.path.join(REN, "data", "our_twitter_sim")
    all_mal = set()
    for root, _, files in sorted(os.walk(data)):
        for name in sorted(files):
            if not name.endswith(".csv"):
                continue
            path = os.path.join(root, name)
            mal = ben = in_coaid = in_fnn = neither = ben_real = 0
            for _, typ, posts in agent_posts(path):
                for p in posts:
                    if "bad" in typ:
                        mal += 1
                        all_mal.add(p)
                        a, b = p in coaid_fake, p in fnn
                        in_coaid += a
                        in_fnn += b
                        neither += not (a or b)
                    else:
                        ben += 1
                        ben_real += p in coaid_real
            rel = os.path.relpath(path, data).replace("\\", "/")
            print(f"{rel:78s} {mal:9d} {in_coaid:6d} {in_fnn:5d} {neither:7d} | {ben:9d} {ben_real:10d}")

    print(f"\nDistinct malicious posts across all files: {len(all_mal)}; "
          f"in CoAID fake titles: {sum(p in coaid_fake for p in all_mal)}; "
          f"in FakeNewsNet titles: {sum(p in fnn for p in all_mal)}")

    print("\nWhere user 900's nine starting posts sit in CoAID (decentralised nodefense file):")
    f = os.path.join(data, "nodefense", "test_1000_good_bad_random_bernoulli_wlx_nodefense.csv")
    for uid, _, posts in agent_posts(f):
        if uid == 900:
            for p in posts:
                loc = coaid_fake.get(p)
                where = f"{loc[0]} line {loc[1]} (row id {loc[2]})" if loc else "not found"
                print(f"  {p[:70]:70s} -> {where}")


if __name__ == "__main__":
    main()
