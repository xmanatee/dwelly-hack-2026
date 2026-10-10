"""One palette and Plotly template; figure-specific units and meaning belong to recipes."""

from typing import Any

TOKENS = {
    "ink": "#202624",
    "muted": "#67706b",
    "line": "#e3e6e0",
    "paper": "#f7f8f5",
    "accent": "#326450",
    "red": "#b74d43",
    "amber": "#947126",
    "blue": "#516c90",
    "surface": "#ffffff",
    "soft": "#f0f3ed",
    "fail-soft": "#fae6df",
    "warn-soft": "#f4edd8",
    "on-ink": "#edf3ec",
    "shade": "#17281e55",
    "radius": "12px",
    "font": "Inter, ui-sans-serif, system-ui, -apple-system, sans-serif",
}
DISPLAY = {"decimals": 2, "small_digits": 2, "percent_decimals": 1, "page_size": 12}

PALETTE = [TOKENS["accent"], TOKENS["blue"], "#ac8865", "#7b7598", "#6b9390", "#8e9c68"]


def css() -> str:
    return (
        ":root{"
        + ";".join(f"--{key}:{value}" for key, value in TOKENS.items())
        + ";color-scheme:light}"
    )


def styled(figure: Any) -> Any:
    from plotly import graph_objects as go

    result = go.Figure(figure)  # Presentation changes never mutate the caller's figure.
    axis = {
        "automargin": True,
        "gridcolor": TOKENS["line"],
        "zeroline": False,
        "ticks": "",
        "showline": False,
        "tickformat": f",.{DISPLAY['decimals']}~f",
    }
    result.update_layout(
        template=go.layout.Template(
            layout={
                "font": {"family": TOKENS["font"], "size": 12, "color": TOKENS["ink"]},
                "colorway": PALETTE,
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "xaxis": axis,
                "yaxis": axis,
                "hoverlabel": {"bgcolor": "white", "font_size": 12},
                "legend": {"orientation": "h", "y": 1.05, "yanchor": "bottom", "x": 0},
                "margin": {"t": 70, "r": 25, "b": 50, "l": 25},
            }
        )
    )
    if result.layout.height is None:
        result.update_layout(height=340)
    return result
