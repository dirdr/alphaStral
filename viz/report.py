"""Assembles chart figures into a single self-contained HTML benchmark report."""

from __future__ import annotations

import datetime

import plotly.io as pio

from viz.charts import (
    action_type_ratio,
    cumulative_win_rate,
    fallback_timeline,
    game_length_histogram,
    latency_by_turn,
    latency_violin,
    outcome_timeline,
    win_rate_bar,
)

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #0e0e0e;
    color: #e0e0e0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    padding: 2.5rem 3rem;
    max-width: 1400px;
    margin: 0 auto;
}
header { margin-bottom: 2.5rem; }
h1 { font-size: 1.5rem; font-weight: 600; letter-spacing: -0.02em; }
.meta { color: #666; font-size: 0.85rem; margin-top: 0.4rem; }
.meta span { margin-right: 1.5rem; }
h2 {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #555;
    margin: 2.5rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e1e1e;
}
.charts { display: flex; flex-wrap: wrap; gap: 1rem; }
.chart { flex: 1 1 560px; min-width: 0; background: #141414; border-radius: 8px; overflow: hidden; }
.chart-full { flex: 1 1 100%; background: #141414; border-radius: 8px; overflow: hidden; }
"""

_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AlphaStral — {p1} vs {p2}</title>
  <style>{css}</style>
</head>
<body>
  <header>
    <h1>AlphaStral Benchmark</h1>
    <p class="meta">
      <span>{p1} vs {p2}</span>
      <span>{n_games} battles</span>
      <span>{date}</span>
    </p>
  </header>

  <h2>Overview</h2>
  <div class="charts">
    <div class="chart-full">{win_rate_bar}</div>
    <div class="chart">{game_length_histogram}</div>
    <div class="chart">{cumulative_win_rate}</div>
  </div>

  <h2>Battle Sequence</h2>
  <div class="charts">
    <div class="chart-full">{outcome_timeline}</div>
  </div>

  {llm_section}
</body>
</html>
"""

_LLM_SECTION = """\
  <h2>LLM Decision Analysis</h2>
  <div class="charts">
    <div class="chart">{latency_violin}</div>
    <div class="chart">{latency_by_turn}</div>
    <div class="chart">{action_type_ratio}</div>
    <div class="chart">{fallback_timeline}</div>
  </div>
"""


def _fig_div(fig, *, first: bool) -> str:
    return pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=first,
        config={"displayModeBar": False, "responsive": True},
    )


def build_report(data: dict) -> str:
    s = data["summary"]
    battles = data["battles"]
    ts = data["turn_stats"]
    p1, p2 = s["p1_agent"], s["p2_agent"]

    winners = [b["winner"] for b in battles]
    n_turns = [b["n_turns"] for b in battles]

    figs = [
        win_rate_bar(p1, p2, s["p1_wins"], s["p2_wins"], s["draws"], s["n_games"]),
        game_length_histogram(n_turns),
        cumulative_win_rate(winners, p1),
        outcome_timeline(winners, p1, p2),
    ]

    divs = [_fig_div(fig, first=(i == 0)) for i, fig in enumerate(figs)]

    llm_section = ""
    if ts:
        llm_figs = [
            latency_violin(ts, p1, p2),
            latency_by_turn(ts, p1),
            action_type_ratio(ts, p1, p2),
            fallback_timeline(ts, p1),
        ]
        llm_divs = [_fig_div(fig, first=False) for fig in llm_figs]
        llm_section = _LLM_SECTION.format(
            latency_violin=llm_divs[0],
            latency_by_turn=llm_divs[1],
            action_type_ratio=llm_divs[2],
            fallback_timeline=llm_divs[3],
        )

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    return _HTML.format(
        css=_CSS,
        p1=p1,
        p2=p2,
        n_games=s["n_games"],
        date=date,
        win_rate_bar=divs[0],
        game_length_histogram=divs[1],
        cumulative_win_rate=divs[2],
        outcome_timeline=divs[3],
        llm_section=llm_section,
    )
