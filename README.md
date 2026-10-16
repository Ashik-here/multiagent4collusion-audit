# MultiAgent4Collusion audit

This repo has my notes and scripts from checking the code released with Ren et al. (2025),
*When Autonomy Goes Rogue: Preparing for Risks of Multi-Agent Collusion in Social Systems*
([arXiv:2507.14660](https://arxiv.org/abs/2507.14660)). I did it for my FOSE7901 research placement at Macquarie
University, alongside a literature review of the paper's methods.

Basically I wanted to know whether the released code actually does what the paper says. I went through the code
and data at one fixed commit, compared the settings with the paper, and wrote a few small scripts to recount
anything countable. I didn't run the simulation itself (it needs GPU model servers), so everything here is from
reading the files.

## Sources

| Source | Version |
|---|---|
| [renqibing/MultiAgent4Collusion](https://github.com/renqibing/MultiAgent4Collusion) (the paper's code) | commit `b6daeff24883a4c253858c4dab3261383f888243` (19 July 2025) |
| The paper | arXiv 2507.14660, version 2 (24 July 2025) |
| [camel-ai/oasis](https://github.com/camel-ai/oasis) (the simulator it's built on) | commits given where used |
| [cuilimeng/CoAID](https://github.com/cuilimeng/CoAID) (COVID-19 misinformation dataset) | commit `d238224346781255e1e7e6ed8bc410c2b2e6329e` |
| [KaiDMML/FakeNewsNet](https://github.com/KaiDMML/FakeNewsNet) (the dataset the paper names) | commit `654361e1c8d5baa751baf1dac5032df621652280` |

Version 1 of the paper links to `renqibing/RogueAgent`. That link now redirects to MultiAgent4Collusion, so it's the
same repo, just renamed.

## What I found

There's more detail, with links to the exact lines, in [FINDINGS.md](FINDINGS.md).

**What the IDs mean:** the letter is the group and the number is the finding within it.

- **A** = how often agents act (the activation rule and turn counts)
- **B** = where the misinformation posts come from
- **C** = other checks against the paper, including what's missing from the release
- **D** = points from my first read of the code that I went back and re-checked

| ID | Finding | Status |
|---|---|---|
| A1–A4 | The paper says agents act with probability 0.02 per step, but the code rescales the stored values, so in decentralised runs agents act at about 0.19–0.20 per step (roughly ten times more). | Confirmed |
| A7, A4 | In centralised runs the leader is always active, and that changes the rescaling for everyone else. The same 1,000 agents get about 37% fewer turns than in the decentralised file, benign agents included. | Confirmed |
| A5 | Malicious agents get very different numbers of turns depending on the setting (about 1,283 centralised, 1,885–2,006 decentralised, 10 for the single agent), even though every setting starts them with 900 posts. | Partly confirmed |
| D6–D8, C5 | In the banning experiment, every malicious reflection uses the "detection evasion" prompt, detection rounds check fixed groups, and the detector is gpt-4o-mini reading each agent's whole post and comment history. | Confirmed |
| B1–B5 | The misinformation posts are exact titles from CoAID, not FakeNewsNet, and the paper doesn't cite CoAID. | Confirmed (44 of 45 data files) |
| C1–C4, D2, D3 | Missing from the release: the e-commerce fraud experiment, the 10/30/60-agent files for Figure 4, a way to run the "no message" ban condition, and any results. The single-agent and "only good" baselines also don't work the way the paper describes. | Confirmed |
| C6–C12, D4 | Smaller differences (clustering, feed settings) and some problems that stop the code running as released. | Confirmed or partly |
| C13, D9 | Things that do match the paper: the Appendix D prompts and the de-bunking setup. | Confirmed |

The IDs match my research records and the table in my literature review, so some numbers are skipped. Anything I
couldn't confirm I left out. Two things I noticed but couldn't settle are in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

## Running the checks

I used git, bash, curl and Python 3.8+. The scripts only use the standard library, and none of them runs or
imports the repo's own code.

```bash
bash scripts/get_sources.sh                                     # clones the pinned versions into ./sources
python scripts/turn_counts.py  > results/turn_counts_output.txt  # activation and expected turns
python scripts/source_check.py > results/source_check_output.txt # where the posts come from
bash scripts/hash_check.sh     > results/hash_check_output.txt   # byte-for-byte file comparisons
```

`results/` has the output from my own run. I used Windows 11 with Python 3.13.3, git 2.48.1 and Git Bash (bash 5.2).
The sources take up about 190 MB.

## Limits

- I read the code but didn't run the simulation. The published results might have come from code or settings that
  were never released, so this is about the release, not necessarily what made the paper's figures.
- The turn counts are expected values (averages over many runs), not counts from actual runs.
- A "turn" is one call to an agent's language model. One turn can lead to several actions or none, so turns and
  actions aren't the same thing.

I used Claude Code to help me understand the codebase.

## Licence

My scripts are MIT licensed and my notes are CC BY 4.0. The short code excerpts from MultiAgent4Collusion and OASIS
(both Apache 2.0) are quoted with links back to the original lines, and quotes from the paper are from Ren et al.
(2025), CC BY 4.0. No third-party data is stored here; `get_sources.sh` downloads it from the original repos.
[CITATION.cff](CITATION.cff) has citation details.

Ren, Q., Xie, S., Wei, L., Yin, Z., Yan, J., Ma, L., & Shao, J. (2025). *When autonomy goes rogue: Preparing for
risks of multi-agent collusion in social systems* (arXiv:2507.14660). https://doi.org/10.48550/arXiv.2507.14660
