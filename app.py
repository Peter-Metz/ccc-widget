import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

base_asset_df = pd.read_csv("baseline_results_assets.csv")
base_asset_df["policy"] = "base"

biden_asset_df = pd.read_csv("biden_results_assets.csv")
biden_asset_df["policy"] = "biden"

asset_df_all = pd.concat([base_asset_df, biden_asset_df])
asset_df = asset_df_all.drop(
    ["Unnamed: 0", "metr_d", "metr_e", "metr_mix", "z_mix"], axis=1
)

base_industry_df = pd.read_csv("baseline_byindustry.csv")
base_industry_df["policy"] = "base"

biden_industry_df = pd.read_csv("biden_industry_results.csv")
biden_industry_df["policy"] = "biden"

industry_df_all = pd.concat([base_industry_df, biden_industry_df])
industry_df = industry_df_all.loc[
    (industry_df_all["Industry"] == industry_df_all["major_industry"])
    & (industry_df_all["major_industry"] != "overall")
]
industry_df = industry_df.drop(
    ["Unnamed: 0", "bea_ind_code", "metr_d", "metr_e", "metr_mix", "z_mix"], axis=1
)


def make_fig(year, tax_treat, financing):
    """
    function to make Plotly figure
    will be called in app callback
    """

    def make_data(pol, year, tax_treat):
        """
        filter data by policy, year, and tax treatment
        omit 'overall' asset type because it messes with the bubble scaling
        """
        if tax_treat == "overall":
            asset_data = asset_df.loc[
                (asset_df["asset_name"] != "Overall")
                & (asset_df["policy"] == pol)
                & (asset_df["year"] == year)
            ]

            industry_data = industry_df.loc[
                (industry_df["Industry"] != "Overall")
                & (industry_df["policy"] == pol)
                & (industry_df["year"] == year)
            ]

        else:
            asset_data = asset_df.loc[
                (asset_df["asset_name"] != "Overall")
                & (asset_df["policy"] == pol)
                & (asset_df["tax_treat"] == tax_treat)
                & (asset_df["year"] == year)
            ]
            asset_data["assets_ovr"] = asset_data["assets"]

            industry_data = industry_df.loc[
                (industry_df["Industry"] != "Overall")
                & (industry_df["policy"] == pol)
                & (industry_df["tax_treat"] == tax_treat)
                & (industry_df["year"] == year)
            ]
            industry_data["assets_ovr"] = industry_data["assets"]
        return asset_data, industry_data

    base_asset, base_industry = make_data("base", year, tax_treat)
    biden_asset, biden_industry = make_data("biden", year, tax_treat)

    def calc_overall_treat(pol, var):
        for mettr in ["mettr_d", "mettr_e", "mettr_mix"]:
            mettr_tot = mettr + "_tot"
            pol[mettr_tot] = pol["assets"] * pol[mettr]

            g = pol.groupby(var)
            sr = g.apply(lambda x: x[mettr_tot].sum()) / g.apply(
                lambda x: x["assets"].sum()
            )
            sr_size = g.apply(lambda x: x["assets"].sum())

            mettr_ovr = mettr + "_ovr"
            pol[mettr_ovr] = pol[var].map(sr)
            pol["assets_ovr"] = pol[var].map(sr_size)
        return pol

    if tax_treat == "overall":
        base_asset = calc_overall_treat(base_asset, "asset_name")
        biden_asset = calc_overall_treat(biden_asset, "asset_name")
        base_industry = calc_overall_treat(base_industry, "Industry")
        biden_industry = calc_overall_treat(biden_industry, "Industry")
        financing = financing + "_ovr"

    # scale the size of the bubbles

    sizeref = 2.0 * max(base_asset.assets_ovr / (60.0 ** 2))
    # sizeref_industry = 2. * max(base_industry.assets_ovr / (60.**2))

    def make_traces(base_data, biden_data, y):
        base_trace = go.Scatter(
            x=base_data[financing],
            y=base_data[y],
            marker=dict(size=base_data["assets_ovr"], sizemode="area", sizeref=sizeref),
            mode="markers",
            name="Current Law",
            hovertemplate="<b>%{y}</b><br>"
            + "<i>Current Law</i><br><br>"
            + "Asset Size: $%{marker.size:.3s}<br>"
            + "METTR: %{x:.1%}<extra></extra>",
            hoverlabel=dict(bgcolor="#b3c6ff"),
        )

        biden_trace = go.Scatter(
            x=biden_data[financing],
            y=biden_data[y],
            marker=dict(
                size=biden_data["assets_ovr"], sizemode="area", sizeref=sizeref
            ),
            mode="markers",
            name="Biden 2020 Proposal",
            hovertemplate="<b>%{y}</b><br>"
            + "<i>Biden 2020 Proposal</i><br><br>"
            + "Asset Size: $%{marker.size:.3s}<br>"
            + "METTR: %{x:.1%}<extra></extra>",
            hoverlabel=dict(bgcolor="#f3bebe"),
        )

        layout = go.Layout(
            title="Marginal Effective Tax Rates on Capital by Asset",
            xaxis=dict(
                title="Marginal Effective Tax Rate",
                gridcolor="#f2f2f2",
                tickformat="%",
                #         range=[-0.15,0.3]
            ),
            yaxis=dict(gridcolor="#f2f2f2", type="category"),
            paper_bgcolor="white",
            plot_bgcolor="white",
            width=1000,
        )

        fig = go.Figure(data=[base_trace, biden_trace], layout=layout)
        return fig

    fig_asset = make_traces(base_asset, biden_asset, "asset_name")
    fig_industry = make_traces(base_industry, biden_industry, "Industry")

    fig_asset.layout.height = 500
    fig_industry.layout.height = 700

    # fix the x-axis when changing years
    if financing == "mettr_e" and tax_treat == "corporate":
        fig_asset.layout.xaxis.range = [-0.05, 0.5]
    elif financing == "mettr_e" and tax_treat == "non-corporate":
        fig_asset.layout.xaxis.range = [-0.18, 0.38]
    elif financing == "mettr_d" and tax_treat == "corporate":
        fig_asset.layout.xaxis.range = [-0.45, 0.38]
    elif financing == "mettr_d" and tax_treat == "non-corporate":
        fig_asset.layout.xaxis.range = [-0.22, 0.42]
    elif financing == "mettr_mix" and tax_treat == "corporate":
        fig_asset.layout.xaxis.range = [-0.07, 0.45]
    elif financing == "mettr_mix" and tax_treat == "non-corporate":
        fig_asset.layout.xaxis.range = [-0.20, 0.37]
    elif financing == "mettr_d_ovr" and tax_treat == "overall":
        fig_asset.layout.xaxis.range = [-0.40, 0.42]
    elif financing == "mettr_mix_ovr" and tax_treat == "overall":
        fig_asset.layout.xaxis.range = [-0.08, 0.45]
    elif financing == "mettr_e_ovr" and tax_treat == "overall":
        fig_asset.layout.xaxis.range = [-0.05, 0.45]

    return fig_asset, fig_industry


app = dash.Dash(external_stylesheets=external_stylesheets)
# layout can be thought of as HTML elements
app.layout = html.Div(
    [
        html.Div(
            [
                # year slider
                html.Label("Year"),
                dcc.Slider(
                    id="year",
                    value=2020,
                    min=2020,
                    max=2026,
                    step=1,
                    marks={
                        2020: "2020",
                        2021: "2021",
                        2022: "2022",
                        2023: "2023",
                        2024: "2024",
                        2025: "2025",
                        2026: "2026",
                    },
                ),
            ],
            style={
                "width": "300px",
                "display": "inline-block",
                "padding-right": "30px",
                "padding-bottom": "50px",
            },
        ),
        html.Div(
            [
                # financing dropdown
                html.Label("Financing"),
                dcc.Dropdown(
                    id="financing",
                    options=[
                        {"label": "Typically Financed", "value": "mettr_mix"},
                        {"label": "Equity", "value": "mettr_e"},
                        {"label": "Debt", "value": "mettr_d"},
                    ],
                    value="mettr_mix",
                ),
            ],
            style={
                "width": "200px",
                "display": "inline-block",
                "padding-right": "30px",
            },
        ),
        html.Div(
            [
                # tax treatment dropdown
                html.Label("Tax Treatment"),
                dcc.Dropdown(
                    id="treatment",
                    options=[
                        {"label": "Overall", "value": "overall"},
                        {"label": "Corporate", "value": "corporate"},
                        {"label": "Non-Corporate", "value": "non-corporate"},
                    ],
                    value="overall",
                ),
            ],
            style={"width": "200px", "display": "inline-block"},
        ),
        html.Div(
            [
                dcc.Tabs(
                    id="tabs",
                    value="asset_tab",
                    children=[
                        dcc.Tab(label="METR by Asset", value="asset_tab"),
                        dcc.Tab(label="METR by Industry", value="industry_tab"),
                    ],
                )
            ],
            style={"max-width": "1000px"},
        ),
        html.Div([dcc.Graph(id="fig_tab")], style={"max-width": "1000px"}),
    ]
)


@app.callback(
    # output is figure
    Output("fig_tab", "figure"),
    # inupts are widget values
    [
        Input("year", "value"),
        Input("financing", "value"),
        Input("treatment", "value"),
        Input("tabs", "value"),
    ],
)
def update(year, financing, treatment, tab):
    # call function that constructs figure
    fig_assets, fig_industry = make_fig(year, treatment, financing)
    if tab == "asset_tab":
        return fig_assets
    elif tab == "industry_tab":
        return fig_industry


# turn debug=False for production
if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)
