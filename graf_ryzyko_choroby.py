"""
Graf powiązań Risk Factors → Choroby z wagami β (Hazard Ratio).

Pokazuje 3 widoki na jednym HTML:
  1. Sankey diagram — przepływy proporcjonalne do β
  2. Sieć dwudzielna (network) — RF na lewo, choroby na prawo, krawędzie z HR
  3. Heatmapa HR — pełna macierz

Wartości pobierane bezpośrednio z DiseaseModel.HAZARD_BETA — żaden parametr
nie jest tu hardkodowany, więc graf automatycznie odzwierciedla zmiany w modelu.
"""
import math
from disease_model import DiseaseModel


# Krótkie polskie etykiety dla RF (zachowane mapowanie 1:1 z citizen.py)
RF_LABELS = {
    "smoking":              "Palenie",
    "obesity":              "Otyłość (BMI)",
    "physical_inactivity":  "Brak aktywności",
    "alcohol_abuse":        "Nadużywanie alkoholu",
    "high_cholesterol":     "Hipercholesterolemia",
    "hypertension_stage0":  "Nadciśnienie (pre)",
    "family_history":       "Historia rodzinna",
}

# Kolory dla risk factors
RF_COLORS = {
    "smoking":              "#34495e",
    "obesity":              "#e67e22",
    "physical_inactivity":  "#95a5a6",
    "alcohol_abuse":        "#8e44ad",
    "high_cholesterol":     "#f39c12",
    "hypertension_stage0":  "#16a085",
    "family_history":       "#7f8c8d",
}

DISEASE_COLORS = {
    "CVD":         "#c0392b",
    "Lung Cancer": "#2c3e50",
}


def beta_to_hr(beta: float) -> float:
    return math.exp(beta) if beta > 0 else 1.0


def build_edges(disease_model: DiseaseModel):
    """
    Zwraca listę krawędzi: [(rf, disease, beta, hr), ...]
    tylko gdzie β > 0.
    """
    edges = []
    for disease, beta_map in disease_model.HAZARD_BETA.items():
        for rf, beta in beta_map.items():
            if beta > 0:
                edges.append((rf, disease, beta, math.exp(beta)))
    return edges


def create_sankey(disease_model: DiseaseModel):
    import plotly.graph_objects as go

    edges = build_edges(disease_model)
    rfs = list(RF_LABELS.keys())
    diseases = disease_model.diseases

    # Indeksy: najpierw RF, potem choroby
    nodes = [RF_LABELS[r] for r in rfs] + diseases
    node_colors = [RF_COLORS[r] for r in rfs] + [DISEASE_COLORS.get(d, "#7f8c8d") for d in diseases]

    rf_to_idx = {r: i for i, r in enumerate(rfs)}
    disease_to_idx = {d: len(rfs) + i for i, d in enumerate(diseases)}

    source, target, value, label, link_colors = [], [], [], [], []
    for rf, disease, beta, hr in edges:
        source.append(rf_to_idx[rf])
        target.append(disease_to_idx[disease])
        value.append(beta)  # szerokość ∝ β (czyli ∝ ln(HR))
        label.append(f"HR={hr:.2f}, β={beta:.2f}")
        # Kolor krawędzi pochodny od RF (z alfa)
        rf_color = RF_COLORS[rf]
        # Konwersja hex -> rgba z alfa
        r = int(rf_color[1:3], 16)
        g = int(rf_color[3:5], 16)
        b = int(rf_color[5:7], 16)
        link_colors.append(f"rgba({r},{g},{b},0.45)")

    sankey = go.Sankey(
        arrangement="snap",
        node=dict(
            pad=15, thickness=22,
            line=dict(color="white", width=1),
            label=nodes,
            color=node_colors,
            hovertemplate="%{label}<extra></extra>",
        ),
        link=dict(
            source=source, target=target, value=value,
            label=label, color=link_colors,
            hovertemplate="%{source.label} → %{target.label}<br>%{label}<extra></extra>",
        ),
    )
    return sankey


def create_heatmap(disease_model: DiseaseModel):
    import plotly.graph_objects as go

    rfs = list(RF_LABELS.keys())
    diseases = disease_model.diseases

    z = [[beta_to_hr(disease_model.HAZARD_BETA[d].get(rf, 0.0)) for d in diseases] for rf in rfs]
    text = [[f"HR={beta_to_hr(disease_model.HAZARD_BETA[d].get(rf, 0.0)):.2f}" for d in diseases] for rf in rfs]

    heatmap = go.Heatmap(
        z=z,
        x=diseases,
        y=[RF_LABELS[r] for r in rfs],
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=12),
        colorscale="Reds",
        zmin=1.0, zmax=15.0,
        colorbar=dict(title="HR"),
        hovertemplate="%{y} → %{x}<br>HR=%{z:.2f}<extra></extra>",
    )
    return heatmap


def create_network(disease_model: DiseaseModel):
    """
    Network bipartite: RF po lewej, choroby po prawej, krawędzie z grubością ∝ β.
    """
    import plotly.graph_objects as go

    edges = build_edges(disease_model)
    rfs = list(RF_LABELS.keys())
    diseases = disease_model.diseases

    # Pozycje: RF na x=0, choroby na x=1
    rf_y = {r: 1.0 - (i + 0.5) / len(rfs) for i, r in enumerate(rfs)}
    d_y = {d: 1.0 - (i + 0.5) / len(diseases) for i, d in enumerate(diseases)}

    traces = []

    # Krawędzie — każda jako osobny trace, aby ustawić grubość
    max_beta = max((b for _, _, b, _ in edges), default=1.0)
    for rf, disease, beta, hr in edges:
        x0, y0 = 0.0, rf_y[rf]
        x1, y1 = 1.0, d_y[disease]
        width = 1 + 8 * (beta / max_beta)
        rf_color = RF_COLORS[rf]
        r_ = int(rf_color[1:3], 16)
        g_ = int(rf_color[3:5], 16)
        b_ = int(rf_color[5:7], 16)
        traces.append(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(color=f"rgba({r_},{g_},{b_},0.55)", width=width),
            hovertemplate=f"{RF_LABELS[rf]} → {disease}<br>HR={hr:.2f} (β={beta:.2f})<extra></extra>",
            showlegend=False,
        ))

    # Etykiety RF
    traces.append(go.Scatter(
        x=[0.0] * len(rfs),
        y=[rf_y[r] for r in rfs],
        mode="markers+text",
        marker=dict(size=24, color=[RF_COLORS[r] for r in rfs], line=dict(color="white", width=2)),
        text=[RF_LABELS[r] for r in rfs],
        textposition="middle left",
        textfont=dict(size=11),
        showlegend=False,
        hoverinfo="text",
    ))
    # Etykiety chorób
    traces.append(go.Scatter(
        x=[1.0] * len(diseases),
        y=[d_y[d] for d in diseases],
        mode="markers+text",
        marker=dict(size=42, color=[DISEASE_COLORS.get(d, "#7f8c8d") for d in diseases], line=dict(color="white", width=2)),
        text=diseases,
        textposition="middle right",
        textfont=dict(size=13, color="black"),
        showlegend=False,
        hoverinfo="text",
    ))

    return traces


def main():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    dm = DiseaseModel()
    edges = build_edges(dm)

    print("=" * 75)
    print("GRAF POWIĄZAŃ Risk Factors → Choroby")
    print("=" * 75)
    print(f"Risk factors:  {len(RF_LABELS)}")
    print(f"Choroby:       {len(dm.diseases)}  ({', '.join(dm.diseases)})")
    print(f"Krawędzie (β > 0): {len(edges)}")
    print()
    print("Najsilniejsze powiązania (Top 10 HR):")
    for rf, disease, beta, hr in sorted(edges, key=lambda e: -e[3])[:10]:
        print(f"  {RF_LABELS[rf]:25s} → {disease:15s}  HR={hr:5.2f}  (β={beta:.2f})")

    # 3 panele: Sankey + Network + Heatmap
    fig = make_subplots(
        rows=2, cols=2,
        specs=[
            [{"type": "sankey", "colspan": 2}, None],
            [{"type": "xy"},                   {"type": "heatmap"}],
        ],
        subplot_titles=[
            "<b>Sankey: Przepływ ryzyka (szerokość ∝ β = ln HR)</b>",
            "<b>Sieć dwudzielna (grubość krawędzi ∝ β)</b>",
            "<b>Macierz Hazard Ratio</b>",
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
        row_heights=[0.55, 0.45],
    )

    # 1. Sankey
    fig.add_trace(create_sankey(dm), row=1, col=1)

    # 2. Network
    for tr in create_network(dm):
        fig.add_trace(tr, row=2, col=1)

    # 3. Heatmap
    fig.add_trace(create_heatmap(dm), row=2, col=2)

    fig.update_layout(
        title=dict(
            text=(
                "<b>Mapa procesów: Risk Factors → Choroby (model Cox)</b><br>"
                "<sub>Współczynniki β = ln(HR) bezpośrednio z DiseaseModel.HAZARD_BETA</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=16),
        ),
        height=1100, width=1500,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial, sans-serif", size=11),
        showlegend=False,
    )

    # Network panel – wyczyść osie
    fig.update_xaxes(visible=False, range=[-0.4, 1.5], row=2, col=1)
    fig.update_yaxes(visible=False, range=[-0.1, 1.1], row=2, col=1)

    out = "graf_ryzyko_choroby.html"
    fig.write_html(out)
    print(f"\n✓ Zapisano: {out}")


if __name__ == "__main__":
    main()
