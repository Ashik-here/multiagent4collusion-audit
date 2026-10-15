# Findings

For each finding I've written down what the paper says, what the released code or data actually does, and where
to look. Links go to MultiAgent4Collusion at commit `b6daeff24883a4c253858c4dab3261383f888243` unless I say
otherwise. Page numbers are from arXiv version 2 of the paper.

"Confirmed" means the files settle it. "Partly confirmed" means only part of it holds, or the evidence is indirect.

Some terms I use a lot:

- **Turn:** an agent gets activated and the code calls its language model, which picks actions.
- **Stored value:** the activity number saved for each agent for each hour of the day (24 per agent).
- **Threshold:** the stored value after the code rescales it. The chance of a turn at one step equals the
  threshold (capped at 1).

Sections:
1. [How often agents act](#1-how-often-agents-act)
2. [The banning experiment](#2-the-banning-experiment)
3. [Where the posts come from](#3-where-the-posts-come-from)
4. [What isn't in the release](#4-what-isnt-in-the-release)
5. [The baselines](#5-the-baselines)
6. [Other differences from the paper](#6-other-differences-from-the-paper)
7. [Getting it to run](#7-getting-it-to-run)
8. [Things that match the paper](#8-things-that-match-the-paper)

---

## 1. How often agents act

### A1. The activation rule rescales the stored values (Confirmed)

The paper says activation is "modeled as a Bernoulli process (p = 0.02)" (Section 5.1, p. 5). Appendix C.1 (p. 13)
explains that each value is 0.2 with probability 0.1 and 0 otherwise, which averages 0.02. Rescaling isn't
mentioned anywhere.

The code divides every stored value by the largest value in the whole file, adds 0.1 to anything under 0.6, then
rounds ([agents_generator.py, lines 98–104](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/oasis/social_agent/agents_generator.py#L98-L104)):

```python
freq = list(agent_info["activity_level_frequency"])
all_freq = np.array([ast.literal_eval(fre) for fre in freq])
normalized_prob = all_freq / np.max(all_freq)
# Make sure probability is not too small
normalized_prob[normalized_prob < 0.6] += 0.1
normalized_prob = np.round(normalized_prob, 2)
prob_list: list[float] = normalized_prob.tolist()
```

This comes from OASIS. It's in OASIS's first version of the file (October 2024) and still the same at
[commit acd0ee04, lines 88–94](https://github.com/camel-ai/oasis/blob/acd0ee04a8d83dc8d3f1bf01c6d3869d072b700b/oasis/social_agent/agents_generator.py#L88-L94),
but OASIS had removed it by June 2025. It made sense in OASIS because the stored values there were real users'
hourly activity. Here they're just 0 or 0.2. So when 0.2 is the biggest value, a stored 0.2 turns into 1.0 (a turn
every step) and a 0 turns into 0.1. Nobody can go below 0.1, even with a stored value of zero.

I can't tell from the files whether the published runs used this rule, only that the released code does.

### A2. A run covers six hours, and a turn isn't an action (Confirmed)

Each step moves a clock forward by 0.05 hours (3 simulated minutes), starting at 13:00
([twitter_simulation_large.py, lines 444–457](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/twitter_simulation_large.py#L444-L457)).
In a 100-step run the code only ever reads each agent's values for hours 13 to 18 (19, 20, 20, 20, 20 and 1 steps),
so 18 of the 24 hourly values are never used. OASIS takes its start hour from real data and only falls back to
13:00; here it's always 13:00.

A turn is one call to the model. The reply is a list of actions and can include `do_nothing`, and if the reply can't
be read it gets one retry ([agent.py, lines 776–830](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/oasis/social_agent/agent.py#L776-L830)).
Banned agents skip their turns, and reflections run on a separate schedule. The paper doesn't mention the step
length, the start hour or the reflection intervals.

To know how many actions agents really took you'd have to run the model, which I didn't.

### A3 and A4. Expected turns per agent (Confirmed for the released code and data)

`scripts/turn_counts.py` applies the rule to every released data file
([`results/turn_counts_output.txt`](results/turn_counts_output.txt)). These are expected values, ignoring bans.

| Condition (data file) | Agents | Mean stored value | Chance of a turn per step | Expected turns per agent | Expected total for the group |
|---|---|---|---|---|---|
| Decentralised (`nodefense/…wlx_nodefense.csv`) | 100 malicious | 0.0198 | 0.2006 | 20.06 | 2,006.2 |
| | 900 benign | 0.0203 | 0.1996 | 19.96 | 17,963.1 |
| Decentralised, root copy (`test_1000_good_bad_random_bernoulli_wlx.csv`) | 100 malicious | 0.0197 | 0.1885 | 18.85 | 1,884.7 |
| | 900 benign | 0.0196 | 0.1889 | 18.89 | 16,999.2 |
| Centralised (`nodefense/…member…_nodefense.csv`) | 1 leader | 1.0000 | 1.0000 | 100.00 | 100.0 |
| | 99 members | 0.0194 | 0.1195 | 11.95 | 1,182.6 |
| | 900 benign | 0.0196 | 0.1198 | 11.98 | 10,777.6 |
| Single agent (`nodefense/…alone…_nodefense.csv`) | 1 malicious | 0.0333 | 0.1000 | 10.00 | 10.0 |
| | 900 benign | 0.0196 | 0.1889 | 18.89 | 16,999.2 |
| Only good (`nodefense/…onlygood…_nodefense.csv`) | 1 malicious | 0.0000 | 0.1000 | 10.00 | 10.0 |
| | 900 benign | 0.0196 | 0.1889 | 18.89 | 16,999.2 |

The stored values do average about 0.02, like the paper says. It's the rescaling that pushes the chance of acting
up to around 0.19–0.20.

Here's one you can check by hand. Benign user 0 has a stored 0.2 at hour 16 and zeros at hours 13–15, 17 and 18,
in both the root decentralised file and the centralised file:

| File | Largest stored value | Hour 16 | Other hours | Expected turns |
|---|---|---|---|---|
| Decentralised | 0.2 | 0.2 ÷ 0.2 = 1.0 | 0 + 0.1 = 0.1 | 20 × 1.0 + 80 × 0.1 = **28** |
| Centralised | 1.0 (the leader) | 0.2 ÷ 1.0 + 0.1 = 0.3 | 0.1 | 20 × 0.3 + 80 × 0.1 = **14** |

These aren't the turns from the published runs, just what the released code and files would give.

### A7. The centralised file uses the same agents, apart from the leader (Confirmed)

I pulled out each row's 24 activity values from the root decentralised file and from the centralised file and ran
`diff` on them. They're identical for all 1,000 agents, row by row, except row 1,000 (user 999). In the centralised
file that agent is the leader, with all 24 values set to 1. (If you diff the whole files every row looks different,
but that's only because the `created_at` timestamps differ.)

So the one thing that changes between the two conditions is an always-active leader. That alone moves the divisor
in A1 from 0.2 to 1.0, and every other agent's chance of acting drops from about 0.19 to about 0.12 per step. That's
37% fewer turns for the same agents, benign ones included. The coordination comparison in Figure 2 (p. 6) is
therefore comparing two conditions where the whole platform is a lot quieter in the centralised one.

I don't know which decentralised file the published curve used (see A6), or how much of the gap in Figure 2 this
explains.

### A5. "Total number of interactions" (Partly confirmed)

The introduction (p. 2) says the experiments "control for the total number of interactions the malicious agents
have, regardless of the setting".

- **Starting posts are equal.** Every setting gives the malicious agents 900 starting posts in total: 9 each for
  100 agents, or all 900 for the single agent ([`results/source_check_output.txt`](results/source_check_output.txt)).
  That fits the paper's other statement (p. 5) that the number of initial posts is held constant.
- **Turns are not equal.** Malicious agents get about 1,283 turns in total in the centralised file and 1,885–2,006
  in the decentralised files. The single agent gets 10, compared with about 1,900–2,000 for 100 agents.
- **Figure 4 can't be checked.** Its 10, 30 and 60-agent settings aren't released (C2).

It depends what the authors meant by "interactions". If they meant starting posts, the claim holds. If they meant
actions or turns, the released files don't back it up.

### A6. Which data files the plotted curves come from (Partly confirmed)

When you run the simulation on `X.csv`, it saves the results as `post_stats_data_X_<date>.npy`
([line 637](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/twitter_simulation_large.py#L637)).
The plotting code then picks result files by name
([tweet_stats_visualization_metric.py, lines 328–339](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/utils/tweet_stats_visualization_metric.py#L328-L339)):

```python
elif "/centralized" in save_path:
    filter_str = 'post_stats_data_test_1000_good_bad_member_random_bernoulli_wlx'
    title='Centralized Group'
elif "/decentralized" in save_path:
    filter_str = 'post_stats_data_test_1000_good_bad_random_bernoulli_wlx'
    title='Decentralized Group'
```

The centralised one is clear-cut because all six centralised data files are byte-identical. The decentralised filter
matches both the root copy and the `nodefense`/`ban`/`debunking` copies, and those differ a bit (18.9 vs 20.1
expected turns per agent). The `.npy` results aren't in the repo, so I can't see which runs actually went into the
figures.

---

## 2. The banning experiment

### D6. Each detection round checks a different, fixed group (Confirmed)

Before the run starts, the code shuffles the 900 benign and 100 malicious agents into 10 groups of about 90 + 10,
and round *k* only checks group *k*
([twitter_simulation_large.py, lines 352–366 and 515](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/twitter_simulation_large.py#L352-L366)).
That matches "We divided 1000 agents into 10 groups" (p. 6). But it means each round looks at a new set of ten
malicious agents, so changes in recall from round to round (Figure 7b) mix together any adaptation and plain
differences between the groups. I can't say how big the group effect is.

### D7. In ban runs every reflection uses the evasion prompt (Confirmed)

Malicious agents update their reflections every 5 steps. In ban runs this always uses the "detection evasion"
prompt, right from the first update, even before anyone has been banned
([twitter_simulation_large.py, lines 460–465](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/twitter_simulation_large.py#L460-L465);
[agent.py, lines 364–385](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/oasis/social_agent/agent.py#L364-L385)):

```python
if ban:
    ban_message = await self.shared_memory.read_memory("ban_message")
    example_ban_actions = await self.shared_memory.read_memory("example_actions_of_banned_agents")
    reflection_content = restriction_update_prompt.format(
        action_space_prompt=self.action_space_prompt,
        ban_message=ban_message,
        example_ban_actions=example_ban_actions,
        current_reflections=self.reflections,
    )
```

The normal reflection prompt gets the agent's past actions and how its posts did. The ban version gets neither, just
the ban list and the banned agents' actions, and it tells them "You must avoid similar behavior to prevent
detection" (Appendix D.3, p. 17). So comparing runs with and without the ban message changes more than just the
message. What effect that has on behaviour I can't tell without running it.

### D8. The ban message includes agents banned by mistake (Confirmed)

The shared ban message lists every banned agent's ID, plus the last 10 actions of the 3 most recently banned agents
([lines 424–432](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/twitter_simulation_large.py#L424-L432)).
Benign agents who get flagged by mistake go on the same list (lines 533–535). So malicious agents can end up being
shown benign agents' actions as examples of "accomplices" who got caught. How often that happened in practice I
can't know without the results.

### C5. What the detector sees (Confirmed)

The detector is gpt-4o-mini, called through OpenAI's API
([lines 341–351](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/twitter_simulation_large.py#L341-L351)).
The paper calls it a "GPT-4 detector" (p. 6).

It summarises each agent's posts and comments
([agent.py, lines 147–171](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/oasis/social_agent/agent.py#L147-L171)):

```python
for post in self.tweet_stats.posts.values():
    if post.user_id == self.agent_id:
        posts.append(post.content)
    for comment in post.comments:
        if comment.user_id == self.agent_id:
            comments.append({"post_id": post.post_id, "comment": comment.comment})
```

That's every post the agent has ever made, including the 9 misinformation posts it was given at the start (saved
under its ID at lines 252–260), which it can't delete. Likes, reposts, follows and dislikes never go in. The paper
says the summary is based on posts and comments "they have recently created" (Appendix D.4, p. 19). I can't tell how
much the starting posts drove the detector's decisions.

---

## 3. Where the posts come from

### B1 and B2. The misinformation posts are CoAID titles (Confirmed for 44 of the 45 data files)

The paper says "We utilize the Fakenewsnet dataset" (p. 5), but the code points somewhere else:

- [`data/tweets/CoAID/get_tweets.py`, lines 15–22](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/data/tweets/CoAID/get_tweets.py#L15-L22)
  builds `fake_tweets_COVID.json` from the `title` column of CoAID's `NewsFakeCOVID-19.csv`.
- [`agents_init.py`, lines 55–60](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/agents_init.py#L55-L60)
  only loads that file and its "real" version.
- [Lines 188–195](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/agents_init.py#L188-L195)
  give each malicious agent nine posts from it.

`scripts/source_check.py` looks up every starting post as an exact string
([`results/source_check_output.txt`](results/source_check_output.txt)):

- All 917 distinct entries in `fake_tweets_COVID.json` are titles in the official CoAID files.
- In 44 of the 45 data files, every malicious starting post is a CoAID title (900 of 900 in each main file), and
  every benign post is a CoAID real-news title.
- The one exception is `debug.csv`, a 4-agent test file, whose 2 malicious posts are FakeNewsNet (PolitiFact) titles.
- The CoAID files copied into the repo are byte-identical to the official CoAID repo
  ([`results/hash_check_output.txt`](results/hash_check_output.txt), section 3).

Three examples, all from user 900 in the decentralised file:

| Starting post | Official CoAID record |
|---|---|
| Says Tom Hanks has a volleyball to keep him company while heÕs quarantined. | [05-01-2020/NewsFakeCOVID-19.csv, line 387](https://github.com/cuilimeng/CoAID/blob/d238224346781255e1e7e6ed8bc410c2b2e6329e/05-01-2020/NewsFakeCOVID-19.csv?plain=1#L387) |
| You can monitor yourself for COVID-19 with a breath test. | [same file, line 394](https://github.com/cuilimeng/CoAID/blob/d238224346781255e1e7e6ed8bc410c2b2e6329e/05-01-2020/NewsFakeCOVID-19.csv?plain=1#L394) |
| Alkaline diet protects against the coronavirus. | [same file, line 133](https://github.com/cuilimeng/CoAID/blob/d238224346781255e1e7e6ed8bc410c2b2e6329e/05-01-2020/NewsFakeCOVID-19.csv?plain=1#L133) |

(The "Õ" is how CoAID itself stores the apostrophe.) I did this matching once with grep and again with the Python
script, and both gave the same counts. This only covers the released files, of course.

### B3 and B4. FakeNewsNet isn't used by the released agent files (Confirmed)

FakeNewsNet does show up in the repo, but only as a copy of its data-collection code, plus a helper that builds a
"politics" post list from PolitiFact files that aren't included. The agent generator never reads that list.

FakeNewsNet's four dataset files are public on GitHub (commit `654361e1`). None of the 901 distinct malicious posts
used in the 44 CoAID-based files appears in them. The only FakeNewsNet titles in the whole release are the 2 in
`debug.csv`. (The Hugging Face copies linked from the repo's README need a login.)

### B5. CoAID is in the README but not the paper (Confirmed)

The repo's README credits both datasets
([line 165](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/README.md?plain=1#L165)),
but the paper never mentions CoAID. Its reference list only has FakeNewsNet (reference 21).

---

## 4. What isn't in the release

### C1. The e-commerce fraud experiment (Confirmed)

The paper has a second experiment on e-commerce fraud, using "a synthetic dataset that simulates common fraudulent
behaviors" (p. 5), with Figure 3 (good and bad sellers over 20 steps) and Appendix E.

The only e-commerce files in the repo are OASIS's little shop demo: three product ads, 36 users, a "purchase" action
and a sales counter. All six files are byte-identical to OASIS at commit `98da5c21` (5 December 2024)
([`results/hash_check_output.txt`](results/hash_check_output.txt), section 1). I searched the code for seller, buyer,
fraud, review, profit, revenue, refund and similar words and found nothing beyond the demo and some README text. It
might exist somewhere unreleased, but it isn't here.

### C2. The data for Figure 4 (Confirmed)

Figure 4 (p. 6) compares 1, 10, 30, 60 and 100 malicious agents, but only the 1-agent and 100-agent files are
released. I searched both file names and file contents for the other three and didn't find them, and they're not in
the Hugging Face dataset either.

### D3. The "no message" ban condition (Confirmed)

Figure 7b (p. 8) compares banning with and without adaptation. The file `…ban_nomessage.csv` is byte-identical to
the normal ban file, and also to the no-defence and de-bunking files. Using the same agents across conditions is
fine in itself. The problem is that the code has no setting or prompt for a no-message run, so the condition can't be
reproduced from the release. There's a 12.8 KB database journal fragment from a run with that name in the repo
(see D2), so those runs did happen. I just can't see how they were set up.

### D2. Results and seeds (Partly confirmed)

No results are released: no result arrays, databases or logs. The only trace of a run is a journal fragment,
`data/simu_db/yaml_200/ban/test_1000_good_bad_random_bernoulli_wlx_ban_nomessage.db-journal`, with bits of agent
actions in it. The agent files were generated with a fixed seed (`agents_init.py`, line 14), and the simulation runs
weren't seeded, which matches the paper's "Our experiment did not fix the random number seed" (p. 5).

---

## 5. The baselines

### C3. The single malicious agent (Confirmed)

The paper compares many agents with "a single high-activation-rate agent" (p. 5). In the released files, though, the
single agent's stored activity falls outside hours 13–18, so it just gets the 0.1 floor. That's 10 expected turns,
about half of an average benign agent's 18.9 (A3/A4).

It also gets the group prompt. Its own prompt is switched off by a `//` in the key name
([system_prompt(dynamic).json, lines 27–30](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/system_prompt%28dynamic%29.json#L27-L30)).
JSON doesn't have comments, so this just renames the key, and the code falls back to the default malicious prompts
([agent.py, lines 678–681](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/oasis/social_agent/agent.py#L678-L681)).
The single agent ends up being told "You have 1 partners in total" and that it's "a member of a malicious group".
Whether the published single-agent runs used these files and prompts, I can't tell.

### C4. The "only good" baseline (Confirmed)

The "only good" files (used in Figures 2 and 4) still have one malicious agent in them (type `alone_bad`, row 902)
holding 900 CoAID misinformation posts. All of its stored activity values are 0, which looks like an attempt to keep
it quiet. But the 0.1 floor from A1 still gives it about 10 turns, the same as the single agent. The paper doesn't
define "Only Good", so I'm not sure what it was meant to be.

---

## 6. Other differences from the paper

### C6. Clustering (Confirmed)

The paper says it projects "using UMAP on sentence embeddings ... of reflection outputs" (p. 8), and Figure 10 has
"20 clusters total" (p. 9).

The released code clusters embeddings of the detector's summaries, not the reflections. It uses k-means with 50
clusters, and the plotting function uses PCA
([lines 597–606](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/twitter_simulation_large.py#L597-L606),
[lines 123–130](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/twitter_simulation_large.py#L123-L130)).
Figure 10 is in the repo as `figs/clusters_visualization.png` (same SHA-256 as the arXiv figure), but its colours and
legend don't match what the released plotting function draws. It must have come from other or changed code.

### C8. Two settings that contradict the prompts (Confirmed)

Malicious agents are told the recommender favours "Posts from accounts the user follows" (Appendix D.3, p. 15). But
the run script sets the number of those posts to zero (`following_post_count=0`,
[line 328](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/twitter_simulation_large.py#L328)),
and that number is used as the database `LIMIT`
([platform.py, lines 293–312](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/oasis/social_platform/platform.py#L293-L312)).
Follower counts still go into a popularity score, but a comment in `recsys.py` (line 426) says they're only worked
out once ("Update only once"). That last part is just from reading the code.

Also, the ban config turns shared reflections off
([`debug_bad_ban.yaml`, line 10](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/intervention_simulation/debug_bad_ban.yaml#L10)),
so the "Reflections from other members of your group" line in the malicious prompt always says "None". The paper
reports that peer reflections matter (Section 5.5, p. 8) but doesn't say whether the ban runs had them.

### D4. The default config uses 100 agents (Confirmed)

`scripts/misinformation_simulation/debug_default.yaml` sets `num_agents: 100`
([line 13](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/misinformation_simulation/debug_default.yaml#L13)),
while the paper's default is "900 benign agents and 100 malicious agents" (p. 5).

---

## 7. Getting it to run

### C7. No model version is pinned (Confirmed, except which Llama model was used)

| Role | Where it's set | What it says | Paper |
|---|---|---|---|
| Agents | configs, line 16; `utils/scripts/*.sh` | a local folder called `qwen` | Qwen2.5-7B-Instruct (p. 5) |
| Detector | run script, line 346 | `gpt-4o-mini` | GPT-4 (p. 6) |
| Agent profiles | `generate_profile.py`, line 78 | `gpt-4o` | not stated |
| Llama agents | [`llm_deploy.sh`, lines 1–2](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/llm_deploy.sh#L1-L3) | `Llama-3-8B-Lexi-Uncensored` (with `Meta-Llama-3-8B-Instruct` commented out) | LLaMA3.1-8B-Instruct (p. 21) |

There's no model revision or hash anywhere. I can't tell whether that Llama script is what produced the Appendix D.6
results.

### C9. Dependencies (Confirmed)

`pyproject.toml` and `poetry.lock` are OASIS's files, byte-identical to versions in OASIS's history
([`results/hash_check_output.txt`](results/hash_check_output.txt), section 2), and the package is still called
`oasis-ai`. Two packages that core files import aren't in either file: `aiofiles`
([agent.py, line 23](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/oasis/social_agent/agent.py#L23))
and `matplotlib` (`post_stats.py`, line 10, and the run script, line 36). vLLM, which you need to serve the models,
isn't listed either. Another package might happen to pull these in, though. I didn't install anything to check.

### C10. The run script stops straight away on most machines (Partly confirmed, from reading only)

The run script deletes two environment settings without checking they're there first
([lines 51–52](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/twitter_simulation_large.py#L51-L52)):

```python
del os.environ["http_proxy"]
del os.environ["HTTP_PROXY"]
```

In Python that throws an error if the setting doesn't exist, so the script would stop on any machine without a proxy
set up. Separately, `recsys.py` (lines 49–50) loads a model from `/mnt/petrelfs/...` as soon as it's imported, and
that folder only exists on the authors' cluster. I haven't actually seen it fail, since I didn't run it.

### C11. The configs point to a file that doesn't exist (Confirmed)

All five experiment configs set `csv_path` to a `test.csv` (line 4 in each), but there's no file with that name
anywhere in the repo, so you'd have to guess which of the 45 data files to use. Model folders and server addresses
are also hard-coded to the authors' cluster, in the configs, the vLLM scripts and several source files.

### C12. Run length (Confirmed)

The 100-step run length only appears in the configs (`num_timesteps: 100`, line 6). The paper never says it; you can
only see it from the x-axis of the misinformation figures. The e-commerce figures go to 20 steps, and there's no
e-commerce config at all.

---

## 8. Things that match the paper

### C13. The prompts (Confirmed for the three I re-checked)

I compared three prompts word by word with the boxes in the appendix, after lower-casing everything, straightening
the quote marks and re-joining words split across lines:

| Prompt | Code | Appendix | Result |
|---|---|---|---|
| Malicious system prompt | [static JSON, line 16](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/system_prompt%28static%29.json#L16) and line 28 | D.3, pp. 15–16 | identical (144 words) |
| Detection-evasion reflection | [dynamic JSON, line 67](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/system_prompt%28dynamic%29.json#L67) | D.3, pp. 17–18 | identical apart from a missing space in the paper ("3.Your") |
| Detector's yes/no question | [dynamic JSON, line 8](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/twitter_simulation/align_with_real_world/system_prompt%28dynamic%29.json#L8) | D.4, p. 19 | identical (46 words) |

An earlier, rougher comparison suggested the other appendix prompts match closely too, but I haven't re-checked them
properly, so I'm not counting them. Releasing the exact prompts is a real strength of this work.

### D9. De-bunking (Confirmed)

De-bunking runs once, at step 50, and marks every malicious post that exists at that point (`threshold: 1.0` in
[`debug_bad_debunking.yaml`, lines 31–33](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/scripts/intervention_simulation/debug_bad_debunking.yaml#L31-L33)).
That matches the paper's "marking 100% of bad posts with a warning" (p. 7). Posts made after step 50 don't get a
warning.
