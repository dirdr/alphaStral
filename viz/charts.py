"""Chart factories — one function per chart, each returns a go.Figure."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go

_TEMPLATE = "plotly_dark"
_P1_COLOR = "#6EE7F7"
_P2_COLOR = "#F76E6E"
_DRAW_COLOR = "#888888"


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ── Always-available charts ──────────────────────────────────────────────────


def win_rate_bar(
    p1_agent: str,
    p2_agent: str,
    p1_wins: int,
    p2_wins: int,
    draws: int,
    n_games: int,
) -> go.Figure:
    p1_pct = p1_wins / n_games * 100
    draw_pct = draws / n_games * 100
    p2_pct = p2_wins / n_games * 100

    fig = go.Figure()
    for label, value, color in [
        (p1_agent, p1_pct, _P1_COLOR),
        ("draw", draw_pct, _DRAW_COLOR),
        (p2_agent, p2_pct, _P2_COLOR),
    ]:
        fig.add_trace(
            go.Bar(
                name=label,
                x=[value],
                y=[""],
                orientation="h",
                marker_color=color,
                text=f"{value:.1f}%",
                textposition="inside",
                hovertemplate=f"{label}: {value:.1f}% ({round(value * n_games / 100)}/{n_games})<extra></extra>",
            )
        )

    fig.update_layout(
        title="Win Rate",
        barmode="stack",
        template=_TEMPLATE,
        height=160,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.1),
        margin=dict(t=60, b=20, l=20, r=20),
        xaxis=dict(range=[0, 100], ticksuffix="%", showgrid=False),
        yaxis=dict(showticklabels=False),
    )
    return fig


def cumulative_win_rate(winners: list[str], p1_agent: str) -> go.Figure:
    n = len(winners)
    xs = list(range(1, n + 1))
    running = [sum(1 for w in winners[:i] if w == "p1") / i for i in xs]
    final = running[-1]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=[0.5] * n,
            mode="lines",
            line=dict(color=_DRAW_COLOR, dash="dot", width=1),
            name="random baseline",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=running,
            mode="lines",
            line=dict(color=_P1_COLOR, width=2),
            fill="tonexty",
            fillcolor="rgba(110,231,247,0.08)",
            name=p1_agent,
            hovertemplate="battle %{x}<br>win rate: %{y:.1%}<extra></extra>",
        )
    )
    fig.add_hline(
        y=final,
        line_dash="dash",
        line_color=_P1_COLOR,
        opacity=0.5,
        annotation_text=f"final {final:.1%}",
        annotation_font_color=_P1_COLOR,
    )

    fig.update_layout(
        title=f"Cumulative Win Rate: {p1_agent}",
        template=_TEMPLATE,
        height=320,
        xaxis_title="battle",
        yaxis=dict(title="win rate", tickformat=".0%", range=[0, 1]),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40, l=60, r=20),
    )
    return fig


def outcome_timeline(winners: list[str], p1_agent: str, p2_agent: str) -> go.Figure:
    n = len(winners)
    ncols = math.ceil(math.sqrt(n * 2))
    nrows = math.ceil(n / ncols)

    outcome_to_z = {"p1": 2, "draw": 1, "p2": 0}
    flat = [outcome_to_z[w] for w in winners]
    flat += [None] * (nrows * ncols - n)

    grid = [flat[i * ncols : (i + 1) * ncols] for i in range(nrows)]
    hover = []
    for i in range(nrows):
        row = []
        for j in range(ncols):
            idx = i * ncols + j
            if idx < n:
                row.append(f"#{idx + 1} — {winners[idx].upper()}")
            else:
                row.append("")
        hover.append(row)

    fig = go.Figure(
        go.Heatmap(
            z=grid,
            text=hover,
            hovertemplate="%{text}<extra></extra>",
            colorscale=[[0, _P2_COLOR], [0.5, _DRAW_COLOR], [1, _P1_COLOR]],
            showscale=False,
            zmin=0,
            zmax=2,
        )
    )
    fig.update_layout(
        title=f"Outcome Grid  <span style='color:{_P1_COLOR}'>■ {p1_agent}</span>"
        f"  <span style='color:{_DRAW_COLOR}'>■ draw</span>"
        f"  <span style='color:{_P2_COLOR}'>■ {p2_agent}</span>",
        template=_TEMPLATE,
        height=320,
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False),
        margin=dict(t=60, b=20, l=20, r=20),
    )
    return fig


# ── LLM-only charts (require turn_stats) ────────────────────────────────────


def _agent_color(agent: str, p1_agent: str) -> str:
    """Color by checking if either name is a prefix of the other (handles UUID suffix mismatch)."""
    a, b = agent.lower(), p1_agent.lower()
    if a.startswith(b) or b.startswith(a):
        return _P1_COLOR
    return _P2_COLOR


def latency_violin(
    turn_stats: list[dict],
    p1_agent: str,
    p2_agent: str,
) -> go.Figure:
    df = pd.DataFrame(turn_stats)
    fig = go.Figure()

    for agent in df["agent"].unique():
        color = _agent_color(agent, p1_agent)
        subset = df[df["agent"] == agent]["decision_ms"]
        fig.add_trace(
            go.Violin(
                x=subset,
                name=agent,
                orientation="h",
                side="positive",
                marker_color=color,
                points="outliers",
                hovertemplate="%{x:.0f} ms<extra></extra>",
            )
        )

    fig.update_layout(
        title="Decision Latency Distribution",
        template=_TEMPLATE,
        height=320,
        xaxis=dict(title="latency (ms)", type="log"),
        yaxis_title="agent",
        showlegend=False,
        margin=dict(t=60, b=50, l=20, r=20),
    )
    return fig


def latency_percentile_bars(
    turn_stats: list[dict],
    p1_agent: str,
    p2_agent: str,
) -> go.Figure:
    df = pd.DataFrame(turn_stats)
    percentiles = [25, 50, 75, 95]
    labels = ["p25", "p50", "p75", "p95"]

    fig = go.Figure()
    for agent in df["agent"].unique():
        color = _agent_color(agent, p1_agent)
        rows = df[df["agent"] == agent]["decision_ms"]
        values = [float(np.percentile(rows, p)) for p in percentiles]
        fig.add_trace(
            go.Bar(
                name=agent,
                x=labels,
                y=values,
                marker_color=color,
                text=[f"{v:.0f} ms" for v in values],
                textposition="outside",
                hovertemplate="%{x}: %{y:.0f} ms<extra></extra>",
            )
        )

    fig.update_layout(
        title="Latency Percentiles (p25 / p50 / p75 / p95)",
        template=_TEMPLATE,
        height=320,
        barmode="group",
        xaxis_title="percentile",
        yaxis_title="latency (ms)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=50, l=60, r=20),
    )
    return fig


def switch_rate(
    turn_stats: list[dict],
    p1_agent: str,
    p2_agent: str,
) -> go.Figure:
    df = pd.DataFrame(turn_stats)
    agents = list(df["agent"].unique())

    fig = go.Figure()
    for action, color in [("move", _P1_COLOR), ("switch", _P2_COLOR)]:
        pcts = []
        for agent in agents:
            rows = df[df["agent"] == agent]
            pcts.append((rows["action_type"] == action).sum() / len(rows) * 100)
        fig.add_trace(
            go.Bar(
                name=action,
                x=agents,
                y=pcts,
                marker_color=color,
                text=[f"{p:.1f}%" for p in pcts],
                textposition="inside",
                hovertemplate=f"{action}: %{{y:.1f}}%<extra></extra>",
            )
        )

    fig.update_layout(
        title="Move vs Switch Rate: how often does each agent adapt?",
        template=_TEMPLATE,
        height=320,
        barmode="stack",
        xaxis_title="agent",
        yaxis=dict(title="% of turns", ticksuffix="%", range=[0, 100]),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=60, l=60, r=20),
    )
    return fig


def type_effectiveness_bar(
    turn_stats: list[dict],
    p1_agent: str,
    p2_agent: str,
) -> go.Figure:
    df = pd.DataFrame(turn_stats)
    # Only move turns with a known effectiveness value
    df = df[df["effectiveness"].notna() & (df["action_type"] == "move")]

    def _bucket(v: float) -> str:
        if v == 0:
            return "immune"
        if v < 1:
            return "not very effective"
        if v == 1:
            return "neutral"
        return "super effective"

    df = df.copy()
    df["bucket"] = df["effectiveness"].apply(_bucket)

    buckets = ["immune", "not very effective", "neutral", "super effective"]
    colors = ["#444444", _P2_COLOR, _DRAW_COLOR, _P1_COLOR]

    agents = list(df["agent"].unique())
    fig = go.Figure()
    for bucket, color in zip(buckets, colors, strict=True):
        pcts = []
        for agent in agents:
            rows = df[df["agent"] == agent]
            pct = (rows["bucket"] == bucket).sum() / len(rows) * 100 if len(rows) else 0
            pcts.append(pct)
        fig.add_trace(
            go.Bar(
                name=bucket,
                x=agents,
                y=pcts,
                marker_color=color,
                text=[f"{p:.1f}%" for p in pcts],
                textposition="inside",
                hovertemplate=f"{bucket}: %{{y:.1f}}%<extra></extra>",
            )
        )

    fig.update_layout(
        title="Type Effectiveness: what % of moves hit super effective, neutral, or immune?",
        template=_TEMPLATE,
        height=320,
        barmode="stack",
        xaxis_title="agent",
        yaxis=dict(title="% of damaging moves", ticksuffix="%", range=[0, 100]),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=60, l=60, r=20),
    )
    return fig
