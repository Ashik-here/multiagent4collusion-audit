"""Expected number of turns per agent in the released MultiAgent4Collusion data files.

The paper says agents act with probability 0.02 per step. This applies the activation rule the
way the released code does it (commit b6daeff2) and adds up each agent's chance of acting:

  agents_generator.py lines 98-104:  divide by the file's largest value, +0.1 if below 0.6, round
  twitter_simulation_large.py lines 376, 414, 445-457:  clock starts at 13:00, +0.05 h per step,
      agent acts if random.random() < threshold for that hour

No randomness here, just expected values. Bans are ignored. Standard library only, and the repo's
code is only read as text (never imported or run).

Usage:  python scripts/turn_counts.py [path to MultiAgent4Collusion]
"""
import ast
import csv
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "sources", "MultiAgent4Collusion")
SIM = os.path.join(REPO, "scripts", "twitter_simulation", "align_with_real_world", "twitter_simulation_large.py")
GEN = os.path.join(REPO, "oasis", "social_agent", "agents_generator.py")
DATA = os.path.join(REPO, "data", "our_twitter_sim")
CONFIGS = [os.path.join(REPO, "scripts", "misinformation_simulation", "debug_default.yaml"),
           os.path.join(REPO, "scripts", "intervention_simulation", "debug_bad_ban.yaml"),
           os.path.join(REPO, "scripts", "intervention_simulation", "debug_bad_debunking.yaml"),
           os.path.join(REPO, "scripts", "intervention_simulation", "debug_bad_prebunking.yaml")]

START_HOUR = 13        # twitter_simulation_large.py line 376
HOURS_PER_STEP = 0.05  # twitter_simulation_large.py line 445 (0.05 hours = 3 minutes)

# The files named in utils/tweet_stats_visualization_metric.py (lines 328-339). The defence
# folders hold byte-identical copies of the nodefense files (see hash_check.sh).
MAIN_FILES = [
    ("Decentralised", "nodefense/test_1000_good_bad_random_bernoulli_wlx_nodefense.csv"),
    ("Decentralised (root copy)", "test_1000_good_bad_random_bernoulli_wlx.csv"),
    ("Centralised", "nodefense/test_1000_good_bad_member_random_bernoulli_wlx_nodefense.csv"),
    ("Single agent", "nodefense/test_901_good_alone_bad_random_bernoulli_wlx_nodefense.csv"),
    ("Only good", "nodefense/test_901_good_onlygood_bad_random_bernoulli_wlx_nodefense.csv"),
]


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def check_source_lines():
    """Stop if the lines this script copies are not in the checked-out code."""
    needed = {
        GEN: ["normalized_prob = all_freq / np.max(all_freq)",
              "normalized_prob[normalized_prob < 0.6] += 0.1",
              "normalized_prob = np.round(normalized_prob, 2)"],
        SIM: ["start_hour = 13",
              "for timestep in range(1, num_timesteps + 1):",
              "simulation_time_hour = start_hour + 0.05 * timestep",
              "int(simulation_time_hour % 24)",
              "if agent_ac_prob < threshold:"],
    }
    for path, lines in needed.items():
        text = read_text(path)
        for line in lines:
            if line not in text:
                sys.exit(f"STOP: expected line not found in {path}: {line}")
    print("Source check: all rule lines found in the checked-out code.")


def num_timesteps(path):
    m = re.search(r"^\s*num_timesteps:\s*(\d+)", read_text(path), re.M)
    return int(m.group(1)) if m else None


def np_round2(x):
    # np.round(x, 2) multiplies by 100, rounds half to even and divides by 100.
    # Python's round() also rounds half to even, so this gives the same result.
    return round(x * 100) / 100


def load_agents(path):
    csv.field_size_limit(2**31 - 1)
    agents = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            values = [float(v) for v in ast.literal_eval(row["activity_level_frequency"])]
            if len(values) != 24:
                sys.exit(f"STOP: {path} user {row['user_id']} has {len(values)} hourly values, not 24")
            posts = ast.literal_eval(row["previous_tweets"])
            agents.append({"id": int(row["user_id"]), "type": row["user_type"], "raw": values, "posts": len(posts)})
    return agents


def thresholds(agents):
    peak = max(v for a in agents for v in a["raw"])  # np.max(all_freq): one maximum for the whole file
    for a in agents:
        out = []
        for v in a["raw"]:
            p = v / peak
            if p < 0.6:
                p += 0.1
            out.append(np_round2(p))
        a["thr"] = out
    return peak


def hour_schedule(steps):
    """The hourly value each time step uses, computed the same way as the code."""
    return [int((START_HOUR + HOURS_PER_STEP * t) % 24) for t in range(1, steps + 1)]


def expected_turns(a, schedule):
    return sum(min(1.0, max(0.0, a["thr"][h])) for h in schedule)


def summarise(label, rel, schedule):
    agents = load_agents(os.path.join(DATA, rel))
    peak = thresholds(agents)
    print(f"\n### {label}: {rel}")
    print(f"    agents {len(agents)} | largest raw value in file (divisor) {peak:g}")
    by_type = {}
    for a in agents:
        a["turns"] = expected_turns(a, schedule)
        by_type.setdefault(a["type"], []).append(a)
    for typ, group in sorted(by_type.items()):
        n = len(group)
        raw_mean = sum(sum(a["raw"]) / 24 for a in group) / n
        turns = [a["turns"] for a in group]
        print(f"    {typ:14s} n={n:4d} | mean stored value {raw_mean:.4f} | effective per-step probability "
              f"{sum(turns) / n / len(schedule):.4f} | expected turns per agent {sum(turns) / n:6.2f} "
              f"(min {min(turns):.1f}, max {max(turns):.1f}) | expected total for group {sum(turns):8.1f}")
    return agents


def worked_example(a, schedule, note):
    used = sorted(set(schedule))
    counts = {h: schedule.count(h) for h in used}
    parts = [f"{counts[h]} x {a['thr'][h]:g}" for h in used]
    print(f"    {note}: user_id {a['id']} ({a['type']}), {a['posts']} starting posts")
    print(f"      24 stored values: {a['raw']}")
    print(f"      stored values at hours {used}: {[a['raw'][h] for h in used]}")
    print(f"      thresholds at those hours:     {[a['thr'][h] for h in used]}")
    print(f"      expected turns = {' + '.join(parts)} = {a['turns']:.2f}")


def main():
    check_source_lines()
    steps = {os.path.relpath(c, REPO).replace("\\", "/"): num_timesteps(c) for c in CONFIGS}
    print("num_timesteps in configs:", steps)
    T = steps["scripts/misinformation_simulation/debug_default.yaml"]
    schedule = hour_schedule(T)
    print(f"Hour used at each of the {T} steps (hour: number of steps):",
          {h: schedule.count(h) for h in sorted(set(schedule))})

    print("\n=== Main conditions (files named in the plotting script) ===")
    loaded = {label: summarise(label, rel, schedule) for label, rel in MAIN_FILES}

    print("\n=== Worked examples (first agent of each type, plus first benign agent with an active hour in 13-18) ===")
    used = set(schedule)
    for label, agents in loaded.items():
        print(f"  {label}")
        seen = set()
        for a in agents:
            if a["type"] not in seen:
                seen.add(a["type"])
                worked_example(a, schedule, "first of type")
        for a in agents:
            if "good" in a["type"] and any(a["raw"][h] > 0 for h in used):
                worked_example(a, schedule, "benign agent with an active hour in the window")
                break

    print("\n=== Every released agent file (same rule, same schedule) ===")
    for root, _, files in sorted(os.walk(DATA)):
        for name in sorted(files):
            if name.endswith(".csv"):
                rel = os.path.relpath(os.path.join(root, name), DATA).replace("\\", "/")
                summarise("File", rel, schedule)


if __name__ == "__main__":
    main()
