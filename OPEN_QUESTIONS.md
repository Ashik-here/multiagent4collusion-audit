# Open questions

These are a couple of things I noticed in the plotting code but couldn't settle, because the result files the plots
read (`.npy`) aren't in the repo. They're not findings and I don't rely on them for anything. Only the authors can
really answer them.

Links go to MultiAgent4Collusion at commit `b6daeff24883a4c253858c4dab3261383f888243`.

## Q1 (D11). Is Figure 5a's "Banning" curve from the "no message" runs?

In `utils/tweet_stats_visualization_metric.py`, the function that compares the interventions picks its "Banning"
results with this filter
([lines 219–222](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/utils/tweet_stats_visualization_metric.py#L219-L222)):

```python
ban_filter = 'post_stats_data_test_1000_good_bad_random_bernoulli_wlx_ban_nomessage'
```

Its labels and colours (Without Defense blue, Pre-bunking green, De-bunking red, Banning purple) are the same as
Figure 5a, and the figure's image on arXiv is called `intervention_misinformation_metric.png`. If this is the
function that drew Figure 5a, then the banning curve is from runs without the ban message, not the main banning
condition. I can't tell if it is.

## Q2 (D12). What runs are behind "Without Peer Reflections" in Figure 14?

`visualize_comparison` in `utils/tweet_stats_visualization.py`
([lines 219–241](https://github.com/renqibing/MultiAgent4Collusion/blob/b6daeff24883a4c253858c4dab3261383f888243/utils/tweet_stats_visualization.py#L219-L241))
labels its two curves "With Peer Reflections" (green) and "Without Peer Reflections" (red), like Figure 14. It fills
the first from result files with `good_bad_random` in the name (the decentralised data file) and the second from
names with `good_bad_member` (the centralised data file).

So either the runs without peer reflections were saved under a centralised-looking name, or that curve is actually
comparing coordination modes rather than peer reflections. The released files don't say which.
