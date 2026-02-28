"""Chart factories — one function per chart, each returns a go.Figure."""

from __future__ import annotations

import math
import statistics

import pandas as pd
import plotly.graph_objects as go

_TEMPLATE = "plotly_dark"
_P1_COLOR = "#6EE7F7"
_P2_COLOR = "#F76E6E"
_DRAW_COLOR = "#888888"
_GRID_COLOR = "#2a2a2a"


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


def game_length_histogram(n_turns: list[int]) -> go.Figure:
    mean = statistics.mean(n_turns)
    median = statistics.median(n_turns)

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=n_turns,
            nbinsx=40,
            marker_color=_P1_COLOR,
            opacity=0.8,
            name="battles",
            hovertemplate="turns: %{x}<br>count: %{y}<extra></extra>",
        )
    )
    for value, label, color in [(mean, "mean", "#FFD700"), (median, "median", "#FF8C00")]:
        fig.add_vline(
            x=value,
            line_dash="dash",
            line_color=color,
            annotation_text=f"{label} {value:.1f}",
            annotation_font_color=color,
        )

    fig.update_layout(
        title="Game Length Distribution",
        template=_TEMPLATE,
        height=320,
        xaxis_title="turns",
        yaxis_title="battles",
        showlegend=False,
        margin=dict(t=60, b=40, l=50, r=20),
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
        title=f"Cumulative Win Rate — {p1_agent}",
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


def latency_violin(
    turn_stats: list[dict],
    p1_agent: str,
    p2_agent: str,
) -> go.Figure:
    df = pd.DataFrame(turn_stats)
    fig = go.Figure()

    for agent, color in [(p1_agent, _P1_COLOR), (p2_agent, _P2_COLOR)]:
        subset = df[df["agent"] == agent]["decision_ms"]
        if subset.empty:
            continue
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


def latency_by_turn(turn_stats: list[dict], p1_agent: str) -> go.Figure:
    df = pd.DataFrame(turn_stats)
    df = df[df["agent"] == p1_agent].copy()

    trend = df.groupby("turn")["decision_ms"].median().reset_index()

    sample = df.sample(min(3000, len(df)), random_state=0)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sample["turn"],
            y=sample["decision_ms"],
            mode="markers",
            marker=dict(color=_P1_COLOR, opacity=0.15, size=4),
            name="raw",
            hovertemplate="turn %{x} — %{y:.0f} ms<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=trend["turn"],
            y=trend["decision_ms"],
            mode="lines",
            line=dict(color=_P1_COLOR, width=2),
            name="median per turn",
            hovertemplate="turn %{x} — median %{y:.0f} ms<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"Latency Over Turn Number — {p1_agent}",
        template=_TEMPLATE,
        height=320,
        xaxis_title="turn",
        yaxis_title="latency (ms)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=50, l=60, r=20),
    )
    return fig


def fallback_timeline(turn_stats: list[dict], p1_agent: str) -> go.Figure:
    df = pd.DataFrame(turn_stats)
    df = df[(df["agent"] == p1_agent) & (df["used_fallback"])]

    fig = go.Figure()
    if df.empty:
        fig.add_annotation(
            text="No fallback events recorded",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color=_DRAW_COLOR),
        )
    else:
        battles = sorted(df["battle_tag"].unique())
        battle_idx = {tag: i for i, tag in enumerate(battles)}
        df = df.copy()
        df["battle_idx"] = df["battle_tag"].map(battle_idx)

        fig.add_trace(
            go.Scatter(
                x=df["turn"],
                y=df["battle_idx"],
                mode="markers",
                marker=dict(color=_P2_COLOR, size=6, symbol="x"),
                hovertemplate="battle %{y} · turn %{x}<extra></extra>",
                name="fallback",
            )
        )

    fig.update_layout(
        title=f"Fallback Events — {p1_agent}",
        template=_TEMPLATE,
        height=320,
        xaxis_title="turn",
        yaxis_title="battle",
        showlegend=False,
        margin=dict(t=60, b=50, l=60, r=20),
    )
    return fig


def action_type_ratio(
    turn_stats: list[dict],
    p1_agent: str,
    p2_agent: str,
) -> go.Figure:
    df = pd.DataFrame(turn_stats)
    counts = df.groupby(["agent", "action_type"]).size().reset_index(name="count")

    fig = go.Figure()
    for action, color in [("move", _P1_COLOR), ("switch", _P2_COLOR)]:
        subset = counts[counts["action_type"] == action]
        fig.add_trace(
            go.Bar(
                name=action,
                x=subset["agent"],
                y=subset["count"],
                marker_color=color,
                hovertemplate=f"{action}: %{{y}}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Action Type Distribution",
        template=_TEMPLATE,
        height=320,
        barmode="group",
        xaxis_title="agent",
        yaxis_title="turns",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=60, l=60, r=20),
    )
    return fig
