import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]


def calc_overall_treat(df, var):
    """
    Overall tax treatment is calculated by taking a weighted average
    of corporate and non-corporate METRs (weighted by asset size)
    """
    for mettr in ["mettr_d", "mettr_e", "mettr_mix"]:
        mettr_tot = mettr + "_tot"
        mettr_ovr = mettr + "_ovr"
        df[mettr_tot] = df["assets"] * df[mettr]

        # group by by asset/industry, year, and policy
        g = df.groupby([var, "year", "policy"])
        # calculate weighted average of corporate/non-corporate METRs
        sr = g.apply(lambda x: x[mettr_tot].sum()) / g.apply(
            lambda x: x["assets"].sum()
        )
        # total size of asset
        sr_size = g.apply(lambda x: x["assets"].sum())

        df = pd.merge(
            df, sr.to_frame().rename(columns={0: mettr_ovr}), on=[var, "year", "policy"]
        )

        df = pd.merge(
            df,
            sr_size.to_frame().rename(columns={0: "assets_ovr"}),
            on=[var, "year", "policy"],
        )
    return df.sort_values("assets_ovr")


# read Cost-of-Capital-Calculator output
# combine current law and Biden results
# by asset...
base_asset_df = pd.read_csv("baseline_results_assets.csv")
base_asset_df["policy"] = "base"

biden_asset_df = pd.read_csv("biden_results_assets.csv")
biden_asset_df["policy"] = "biden"

asset_df_all = pd.concat([base_asset_df, biden_asset_df])
asset_df_all = asset_df_all.loc[asset_df_all["asset_name"] != "Overall"]

asset_df_all = calc_overall_treat(asset_df_all, "asset_name")

# create separate dataframe for overall tax treatment
asset_df_overall = pd.DataFrame()
asset_df_overall["asset_name"] = asset_df_all["asset_name"]
asset_df_overall["assets"] = asset_df_all["assets_ovr"]
asset_df_overall["mettr_d"] = asset_df_all["mettr_d_ovr"]
asset_df_overall["mettr_e"] = asset_df_all["mettr_e_ovr"]
asset_df_overall["mettr_mix"] = asset_df_all["mettr_mix_ovr"]
asset_df_overall["tax_treat"] = "overall"
asset_df_overall["year"] = asset_df_all["year"]
asset_df_overall["policy"] = asset_df_all["policy"]

asset_df_all = asset_df_all.drop(
    [
        "Unnamed: 0",
        "metr_d",
        "metr_e",
        "metr_mix",
        "z_mix",
        "assets_ovr",
        "assets_ovr_x",
        "assets_ovr_y",
        "mettr_d_tot",
        "mettr_e_tot",
        "mettr_mix_tot",
        "mettr_d_ovr",
        "mettr_e_ovr",
        "mettr_mix_ovr",
    ],
    axis=1,
)
# stack original df and overall tax treatment df
asset_df = pd.concat([asset_df_all, asset_df_overall])
asset_df = asset_df.sort_values(by=["year", "tax_treat", "policy", "asset_name"])
asset_df = asset_df.round({"assets": 0, "mettr_d": 3, "mettr_e": 3, "mettr_mix": 3})

# combine current law and Biden results
# by industry...
base_industry_df = pd.read_csv("baseline_byindustry.csv")
base_industry_df["policy"] = "base"

biden_industry_df = pd.read_csv("biden_industry_results.csv")
biden_industry_df["policy"] = "biden"

industry_df_all = pd.concat([base_industry_df, biden_industry_df])
# only include major_industries
industry_df_all = industry_df_all.loc[
    (industry_df_all["Industry"] == industry_df_all["major_industry"])
    & (industry_df_all["major_industry"] != "Overall")
    # & (industry_df_all['Industry'] != "Overall")
]

industry_df_all = calc_overall_treat(industry_df_all, "Industry")

# create separate dataframe for overall tax treatment
industry_df_overall = pd.DataFrame()
industry_df_overall["Industry"] = industry_df_all["Industry"]
industry_df_overall["major_industry"] = industry_df_all["major_industry"]
industry_df_overall["assets"] = industry_df_all["assets_ovr"]
industry_df_overall["mettr_d"] = industry_df_all["mettr_d_ovr"]
industry_df_overall["mettr_e"] = industry_df_all["mettr_e_ovr"]
industry_df_overall["mettr_mix"] = industry_df_all["mettr_mix_ovr"]
industry_df_overall["tax_treat"] = "overall"
industry_df_overall["year"] = industry_df_all["year"]
industry_df_overall["policy"] = industry_df_all["policy"]
industry_df_overall.drop_duplicates(inplace=True)

industry_df_all = industry_df_all.drop(
    [
        "Unnamed: 0",
        "bea_ind_code",
        "major_industry",
        "metr_d",
        "metr_e",
        "metr_mix",
        "z_mix",
        "assets_ovr",
        "assets_ovr_x",
        "assets_ovr_y",
        "mettr_d_ovr",
        "mettr_e_ovr",
        "mettr_mix_ovr",
        "mettr_d_tot",
        "mettr_e_tot",
        "mettr_mix_tot",
    ],
    axis=1,
)
# stack original df and overall tax treatment df
industry_df = pd.concat([industry_df_all, industry_df_overall])
industry_df = industry_df.sort_values(by=["year", "tax_treat", "policy", "Industry"])
industry_df = industry_df.round(
    {"assets": 0, "mettr_d": 3, "mettr_e": 3, "mettr_mix": 3}
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
        asset_data = asset_df.loc[
            # (asset_df["asset_name"] != "Overall")
            (asset_df["policy"] == pol)
            & (asset_df["year"] == year)
            & (asset_df["tax_treat"] == tax_treat)
        ]

        industry_data = industry_df.loc[
            # (industry_df["Industry"] != "Overall")
            (industry_df["policy"] == pol)
            & (industry_df["year"] == year)
            & (industry_df["tax_treat"] == tax_treat)
        ]

        return asset_data, industry_data

    base_asset, base_industry = make_data("base", year, tax_treat)
    biden_asset, biden_industry = make_data("biden", year, tax_treat)

    # scale the size of the bubbles
    sizeref = 2.0 * max(base_asset.assets / (60.0 ** 2))

    def make_traces(base_data, biden_data, y, title):
        """
        creates the Plotly traces -- current law and biden data series
        """
        base_trace = go.Scatter(
            x=base_data[financing],
            y=base_data[y],
            marker=dict(
                size=base_data["assets"],
                sizemode="area",
                sizeref=sizeref,
                color="#6495ED",
                opacity=1,
            ),
            mode="markers",
            name="Current Law",
            hovertemplate="<b>%{y}</b><br>"
            + "<i>Current Law</i><br><br>"
            + "Asset Size: $%{marker.size:.3s}<br>"
            + "METR: %{x:.1%}<extra></extra>",
            hoverlabel=dict(bgcolor="#abc6f7"),
        )

        biden_trace = go.Scatter(
            x=biden_data[financing],
            y=biden_data[y],
            marker=dict(
                size=biden_data["assets"],
                sizemode="area",
                sizeref=sizeref,
                color="#FF7F50",
                opacity=1,
            ),
            mode="markers",
            name="Biden 2020 Proposal",
            hovertemplate="<b>%{y}</b><br>"
            + "<i>Biden 2020 Proposal</i><br><br>"
            + "Asset Size: $%{marker.size:.3s}<br>"
            + "METR: %{x:.1%}<extra></extra>",
            hoverlabel=dict(bgcolor="#ffb396"),
        )

        layout = go.Layout(
            title="Marginal Effective Tax Rates on Capital by " + title,
            xaxis=dict(
                title="Marginal Effective Tax Rate",
                gridcolor="#f2f2f2",
                tickformat="%",
                #         range=[-0.15,0.3]
            ),
            yaxis=dict(gridcolor="#f2f2f2", type="category"),
            # paper_bgcolor="#F9F9F9",
            plot_bgcolor="white",
            width=1100,
        )

        fig = go.Figure(data=[base_trace, biden_trace], layout=layout)
        return fig

    fig_asset = make_traces(base_asset, biden_asset, "asset_name", "Asset")
    fig_asset.update_layout(legend_orientation="h", legend=dict(x=-0.15, y=1.05))

    fig_industry = make_traces(base_industry, biden_industry, "Industry", "Industry")
    fig_industry.update_layout(legend_orientation="h", legend=dict(x=-0.35, y=1.05))

    fig_asset.layout.height = 500
    fig_industry.layout.height = 700

    # fix the x-axis when changing years for asset fig
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
    elif financing == "mettr_d" and tax_treat == "overall":
        fig_asset.layout.xaxis.range = [-0.40, 0.42]
    elif financing == "mettr_mix" and tax_treat == "overall":
        fig_asset.layout.xaxis.range = [-0.08, 0.45]
    elif financing == "mettr_e" and tax_treat == "overall":
        fig_asset.layout.xaxis.range = [-0.05, 0.45]

    # fix the x-axis when changing years for industry fig
    if financing == "mettr_e" and tax_treat == "corporate":
        fig_industry.layout.xaxis.range = [0.1, 0.45]
    elif financing == "mettr_e" and tax_treat == "non-corporate":
        fig_industry.layout.xaxis.range = [0.0, 0.35]
    elif financing == "mettr_d" and tax_treat == "corporate":
        fig_industry.layout.xaxis.range = [-0.1, 0.3]
    elif financing == "mettr_d" and tax_treat == "non-corporate":
        fig_industry.layout.xaxis.range = [0.05, 0.4]
    elif financing == "mettr_mix" and tax_treat == "corporate":
        fig_industry.layout.xaxis.range = [0.07, 0.4]
    elif financing == "mettr_mix" and tax_treat == "non-corporate":
        fig_industry.layout.xaxis.range = [0.0, 0.35]
    elif financing == "mettr_d" and tax_treat == "overall":
        fig_industry.layout.xaxis.range = [-0.10, 0.33]
    elif financing == "mettr_mix" and tax_treat == "overall":
        fig_industry.layout.xaxis.range = [0.08, 0.4]
    elif financing == "mettr_e" and tax_treat == "overall":
        fig_industry.layout.xaxis.range = [0.1, 0.4]

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
                    max=2029,
                    step=1,
                    marks={
                        2020: "2020",
                        2021: "2021",
                        2022: "2022",
                        2023: "2023",
                        2024: "2024",
                        2025: "2025",
                        2026: "2026",
                        2027: "2027",
                        2028: "2028",
                        2029: "2029",
                    },
                ),
            ],
            style={
                "width": "450px",
                "display": "inline-block",
                "padding-right": "30px",
                "padding-bottom": "50px",
                # "background-color": "#F9F9F9"
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
                # "background-color": "#F9F9F9"
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
                        dcc.Tab(label="By Asset", value="asset_tab"),
                        dcc.Tab(label="By Industry", value="industry_tab"),
                    ],
                )
            ],
            style={"max-width": "1100px"},
        ),
        html.Div([dcc.Graph(id="fig_tab")]),
        html.Div(
            [
                dash_table.DataTable(
                    id="data_table",
                    columns=[
                        {"name": i, "id": j}
                        for i, j in zip(
                            [
                                "Asset Name",
                                "Asset Size",
                                "METR - Debt",
                                "METR - Equity",
                                "METR - Mix",
                                "Tax Treatment",
                                "Year",
                                "Policy",
                            ],
                            asset_df.columns,
                        )
                    ],
                    data=asset_df.to_dict("records"),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_action="native",
                    page_current=0,
                    page_size=15,
                    style_cell={'font-size': '12px', 'font-family':'HelveticaNeue'}
                )
            ],
            style={"padding-top": "50px", "max-width": "1100px"},
        ),
    ]
)


@app.callback(
    # output is figure
    [
        Output("fig_tab", "figure"),
        Output("data_table", "columns"),
        Output("data_table", "data"),
    ],
    [
        Input("year", "value"),
        Input("financing", "value"),
        Input("treatment", "value"),
        Input("tabs", "value"),
    ],
)
def update(year, financing, treatment, tab):
    # call function that constructs figure
    ind_cols = [
        {"name": i, "id": j}
        for i, j in zip(
            [
                "Industry",
                "Asset Size",
                "METR - Debt",
                "METR - Equity",
                "METR - Mix",
                "Tax Treatment",
                "Year",
                "Policy",
            ],
            industry_df.columns,
        )
    ]
    asset_cols = [
        {"name": i, "id": j}
        for i, j in zip(
            [
                "Asset Name",
                "Asset Size",
                "METR - Debt",
                "METR - Equity",
                "METR - Mix",
                "Tax Treatment",
                "Year",
                "Policy",
            ],
            asset_df.columns,
        )
    ]
    ind_data = industry_df.to_dict("records")
    asset_data = asset_df.to_dict("records")

    fig_assets, fig_industry = make_fig(year, treatment, financing)
    if tab == "asset_tab":
        return fig_assets, asset_cols, asset_data
    elif tab == "industry_tab":
        return fig_industry, ind_cols, ind_data


server = app.server
# turn debug=False for production
if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)
