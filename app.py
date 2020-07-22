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
            (asset_df["asset_name"] != "Overall")
            & (asset_df["policy"] == pol)
            & (asset_df["year"] == year)
            & (asset_df["tax_treat"] == tax_treat)
        ]

        industry_data = industry_df.loc[
            (industry_df["Industry"] != "Overall")
            & (industry_df["policy"] == pol)
            & (industry_df["year"] == year)
            & (industry_df["tax_treat"] == tax_treat)
        ]

        return asset_data, industry_data

    def make_tables(tax_treat, financing):
        """
        prepare tables for raw data shown below plots
        """
        asset_table_base = asset_df.loc[
            (asset_df["policy"] == "base") & (asset_df["tax_treat"] == tax_treat)
        ]
        asset_table_base = asset_table_base.pivot_table(
            index="asset_name", columns="year", values=financing
        )
        asset_table_base = round(asset_table_base.reset_index(), 3)
        asset_table_base.rename(columns={"asset_name": "Asset"}, inplace=True)

        asset_table_biden = asset_df.loc[
            (asset_df["policy"] == "biden") & (asset_df["tax_treat"] == tax_treat)
        ]
        asset_table_biden = asset_table_biden.pivot_table(
            index="asset_name", columns="year", values=financing
        )
        asset_table_biden = round(asset_table_biden.reset_index(), 3)
        asset_table_biden.rename(columns={"asset_name": "Asset"}, inplace=True)

        ind_table_base = industry_df.loc[
            (industry_df["policy"] == "base") & (industry_df["tax_treat"] == tax_treat)
        ]
        ind_table_base = ind_table_base.pivot_table(
            index="Industry", columns="year", values=financing
        )
        ind_table_base = round(ind_table_base.reset_index(), 3)

        ind_table_biden = industry_df.loc[
            (industry_df["policy"] == "biden") & (industry_df["tax_treat"] == tax_treat)
        ]
        ind_table_biden = ind_table_biden.pivot_table(
            index="Industry", columns="year", values=financing
        )
        ind_table_biden = round(ind_table_biden.reset_index(), 3)

        # Resort so that Overall row is at the top
        asset_table_base1 = asset_table_base[asset_table_base["Asset"] == "Overall"]
        asset_table_base2 = asset_table_base[asset_table_base["Asset"] != "Overall"]
        asset_table_base = pd.concat([asset_table_base1, asset_table_base2])

        asset_table_biden1 = asset_table_biden[asset_table_biden["Asset"] == "Overall"]
        asset_table_biden2 = asset_table_biden[asset_table_biden["Asset"] != "Overall"]
        asset_table_biden = pd.concat([asset_table_biden1, asset_table_biden2])

        ind_table_base1 = ind_table_base[ind_table_base["Industry"] == "Overall"]
        ind_table_base2 = ind_table_base[ind_table_base["Industry"] != "Overall"]
        ind_table_base = pd.concat([ind_table_base1, ind_table_base2])

        ind_table_biden1 = ind_table_biden[ind_table_biden["Industry"] == "Overall"]
        ind_table_biden2 = ind_table_biden[ind_table_biden["Industry"] != "Overall"]
        ind_table_biden = pd.concat([ind_table_biden1, ind_table_biden2])

        return asset_table_base, asset_table_biden, ind_table_base, ind_table_biden

    asset_table_base, asset_table_biden, ind_table_base, ind_table_biden = make_tables(
        tax_treat, financing
    )

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

    return (
        fig_asset,
        fig_industry,
        asset_table_base,
        asset_table_biden,
        ind_table_base,
        ind_table_biden,
    )


app = dash.Dash(external_stylesheets=external_stylesheets)
# layout can be thought of as HTML elements
app.layout = html.Div(
    [
        dcc.Markdown(
            """
            ### Effective tax rates on capital under current law and Former Vice President Biden's tax proposal

            *Modeling and design by Matt Jensen, Peter Metz, and Kyle Pomerleau*
            """,
            style={"max-width": "700px", "padding-bottom": "60px", "color": "#4f5866"}
        ),
        html.Div(
            [
                # year slider
                html.Label("Year"),
                dcc.Slider(
                    id="year",
                    value=2021,
                    min=2021,
                    max=2030,
                    step=1,
                    marks={
                        2021: "2021",
                        2022: "2022",
                        2023: "2023",
                        2024: "2024",
                        2025: "2025",
                        2026: "2026",
                        2027: "2027",
                        2028: "2028",
                        2029: "2029",
                        2030: "2030",
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
            style={"max-width": "1050px"},
        ),
        html.Div([dcc.Graph(id="fig_tab")]),
        dcc.Markdown(
            """
            **Note:** This project builds on TK paper by Pomerleau. 
            Data for this project are generated using the open-source 
            [Cost-of-Capital-Calculator](https://github.com/PSLmodels/Cost-of-Capital-Calculator) 
            and [Tax-Calculator](https://github.com/PSLmodels/Tax-Calculator) projects. 
            The code that modifies the underlying models to produce these estimates
            can be found [here](https://github.com/kpomerleau/Cost-of-Capital-Calculator/tree/Tests) 
            and [here](https://github.com/erinmelly/Tax-Calculator/tree/Biden).
            The code that powers this data visualization can be found
            [here](https://github.com/Peter-Metz/ccc-widget).
            """,
            style={"padding-top": "30px", "max-width": "1000px"},
        ),
        dcc.Markdown(
            """
            ##### Current Law
            """,
            style={"padding-top": "30px"},
        ),
        html.Div(
            [
                dash_table.DataTable(
                    id="data_table_base",
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_action="native",
                    style_cell={"font-size": "12px", "font-family": "HelveticaNeue"},
                )
            ],
            style={"max-width": "1000px"},
        ),
        dcc.Markdown(
            """
            ##### Biden Proposal
            """,
            style={"padding-top": "30px"},
        ),
        html.Div(
            [
                dash_table.DataTable(
                    id="data_table_biden",
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_action="native",
                    style_cell={"font-size": "12px", "font-family": "HelveticaNeue"},
                )
            ],
            style={"max-width": "1000px"},
        ),
    ]
)


@app.callback(
    # output is figure
    [
        Output("fig_tab", "figure"),
        Output("data_table_base", "columns"),
        Output("data_table_base", "data"),
        Output("data_table_biden", "columns"),
        Output("data_table_biden", "data"),
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

    fig_assets, fig_industry, asset_table_base, asset_table_biden, ind_table_base, ind_table_biden = make_fig(
        year, treatment, financing
    )

    columns_asset = [{"name": str(i), "id": str(i)} for i in asset_table_base.columns]
    data_asset_base = asset_table_base.to_dict("records")
    data_asset_biden = asset_table_biden.to_dict("records")

    columns_ind = [{"name": str(i), "id": str(i)} for i in ind_table_base.columns]
    data_ind_base = ind_table_base.to_dict("records")
    data_ind_biden = ind_table_biden.to_dict("records")

    if tab == "asset_tab":
        return (
            fig_assets,
            columns_asset,
            data_asset_base,
            columns_asset,
            data_asset_biden,
        )
    elif tab == "industry_tab":
        return fig_industry, columns_ind, data_ind_base, columns_ind, data_ind_biden


server = app.server
# turn debug=False for production
if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)
