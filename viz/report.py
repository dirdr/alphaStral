"""Assembles chart figures into a single self-contained HTML benchmark report."""

from __future__ import annotations

import datetime

import plotly.io as pio

from viz.charts import (
    cumulative_win_rate,
    latency_percentile_bars,
    latency_violin,
    outcome_timeline,
    switch_rate,
    type_effectiveness_bar,
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
.reasoning-log {
    background: #141414;
    border-radius: 8px;
    overflow: auto;
    max-height: 520px;
    font-size: 0.8rem;
}
.reasoning-log table { width: 100%; border-collapse: collapse; }
.reasoning-log th {
    position: sticky; top: 0;
    background: #1a1a1a;
    color: #666;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    font-size: 0.68rem;
    padding: 0.55rem 0.9rem;
    text-align: left;
    border-bottom: 1px solid #2a2a2a;
}
.reasoning-log td {
    padding: 0.45rem 0.9rem;
    border-bottom: 1px solid #1c1c1c;
    vertical-align: top;
    color: #bbb;
}
.reasoning-log tr:last-child td { border-bottom: none; }
.reasoning-log td.dim { color: #555; }
.reasoning-log td.reasoning { color: #999; font-style: italic; }
.eff-se   { color: #6EE7F7; font-weight: 600; }
.eff-nve  { color: #F76E6E; }
.eff-imm  { color: #555; }
.eff-neu  { color: #888; }
"""

_HTML_BASE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AlphaStral: {p1} vs {p2}</title>
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
    <div class="chart">{cumulative_win_rate}</div>
    {switch_rate_slot}
  </div>

  <h2>Battle Sequence</h2>
  <div class="charts">
    <div class="chart-full">{outcome_timeline}</div>
  </div>

  {llm_section}
  {reasoning_section}
</body>
</html>
"""

_LLM_SECTION = """\
  <h2>LLM Decision Analysis</h2>
  <div class="charts">
    <div class="chart">{latency_violin}</div>
    <div class="chart">{latency_percentile_bars}</div>
    <div class="chart-full">{type_effectiveness_bar}</div>
  </div>
"""


def _eff_label(v: float | None) -> str:
    if v is None:
        return '<span class="eff-neu">—</span>'
    if v == 0:
        return '<span class="eff-imm">immune</span>'
    if v < 1:
        return f'<span class="eff-nve">{v}×</span>'
    if v == 1:
        return '<span class="eff-neu">1×</span>'
    return f'<span class="eff-se">{v}×</span>'


def _build_reasoning_section(ts: list[dict]) -> str:
    rows_with_reasoning = [t for t in ts if t.get("reasoning")]
    if not rows_with_reasoning:
        return ""

    rows_html = []
    for t in rows_with_reasoning:
        eff = _eff_label(t.get("effectiveness"))
        move = t.get("move_id") or '<span class="dim">switch</span>'
        rows_html.append(
            f"<tr>"
            f'<td class="dim">{t["battle_tag"].split("-")[-1]}</td>'
            f'<td class="dim">{t["turn"]}</td>'
            f"<td>{move}</td>"
            f"<td>{eff}</td>"
            f'<td class="reasoning">{t["reasoning"]}</td>'
            f"</tr>"
        )

    table = (
        "<table>"
        "<thead><tr>"
        "<th>battle</th><th>turn</th><th>move</th><th>eff</th><th>reasoning</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "</table>"
    )
    return f'\n  <h2>Decision Reasoning Log</h2>\n  <div class="reasoning-log">{table}</div>'


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

    base_figs = [
        win_rate_bar(p1, p2, s["p1_wins"], s["p2_wins"], s["draws"], s["n_games"]),
        cumulative_win_rate(winners, p1),
        outcome_timeline(winners, p1, p2),
    ]
    divs = [_fig_div(fig, first=(i == 0)) for i, fig in enumerate(base_figs)]

    switch_rate_slot = ""
    llm_section = ""
    if ts:
        switch_rate_div = _fig_div(switch_rate(ts, p1, p2), first=False)
        switch_rate_slot = f'<div class="chart">{switch_rate_div}</div>'

        ts_with_effectiveness = [t for t in ts if t.get("effectiveness") is not None]
        llm_figs = [
            latency_violin(ts, p1, p2),
            latency_percentile_bars(ts, p1, p2),
        ]
        llm_divs = [_fig_div(fig, first=False) for fig in llm_figs]
        effectiveness_div = (
            _fig_div(type_effectiveness_bar(ts, p1, p2), first=False)
            if ts_with_effectiveness
            else ""
        )
        llm_section = _LLM_SECTION.format(
            latency_violin=llm_divs[0],
            latency_percentile_bars=llm_divs[1],
            type_effectiveness_bar=effectiveness_div,
        )

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    return _HTML_BASE.format(
        css=_CSS,
        p1=p1,
        p2=p2,
        n_games=s["n_games"],
        date=date,
        win_rate_bar=divs[0],
        cumulative_win_rate=divs[1],
        switch_rate_slot=switch_rate_slot,
        outcome_timeline=divs[2],
        llm_section=llm_section,
        reasoning_section=_build_reasoning_section(ts),
    )
