import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

# Load datasets
df_press = pd.read_csv("data/freedom_stats.csv")
df_lgbtq = pd.read_csv("data/lgbtq_rights.csv")

# Merge on ISO code
df = df_press.merge(df_lgbtq[["ISO", "lgbtq_rights"]], left_on="ISO", right_on="ISO", how="left")

# Metric labels
METRIC_LABELS = {
    "Score": "Press Freedom Index",
    "lgbtq_rights": "LGBTQ+ Rights Index"
}

# Initialize Dash app
app = dash.Dash(__name__)

# App Layout
app.layout = html.Div([
    html.H1(
        "🌍 Global Human Rights",
        style={
            "textAlign": "center",
            "marginTop": "20px",
            "marginBottom": "30px",
            "fontSize": "40px",
            "fontWeight": "bold",
            "color": "#222"
        }
    ),

    # Tabs for dataset selection
    dcc.Tabs(
        id="metric-tabs",
        value="Score",  # default is press freedom
        children=[
            dcc.Tab(label="Press Freedom", value="Score"),
            dcc.Tab(label="LGBTQ Rights", value="lgbtq_rights")
        ]
    ),

    # Everything inside the tab goes here
    html.Div(id="dashboard-content")
])


# Callback to render dashboard depending on tab
@app.callback(
    Output("dashboard-content", "children"),
    Input("metric-tabs", "value")
)
def update_dashboard(selected_metric):
    metric_name = METRIC_LABELS[selected_metric]

    # Dropdown for country search
    dropdown = dcc.Dropdown(
        id="country-search",
        options=[
            {"label": row["country"].strip(), "value": row["ISO"].strip()}
            for _, row in df.iterrows()
            if pd.notnull(row["country"]) and pd.notnull(row["ISO"])
        ],
        placeholder="Search for a country...",
        style={"width": "100%"}
    )

    # Top & bottom 5
    top5 = df.nlargest(5, selected_metric)[["country", selected_metric]]
    bottom5 = df.nsmallest(5, selected_metric)[["country", selected_metric]]

    # Choropleth
    fig = px.choropleth(
        df,
        locations="ISO",
        color=selected_metric,
        hover_name="country",
        hover_data={"ISO": False, selected_metric: True},
        color_continuous_scale="RdYlGn",
        range_color=(df[selected_metric].min(), df[selected_metric].max()),
        title=f"🌍 {metric_name}"
    )
    fig.update_traces(marker_line_width=0.5, marker_line_color="white")
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=False, projection_type="natural earth"),
        margin=dict(l=0, r=0, t=50, b=0)
    )

    # Build the whole layout for the tab
    return html.Div([
        html.Div(dropdown, style={"maxWidth": "400px", "margin": "20px auto"}),

        html.Div([
            # Map + country info (left)
            html.Div([
                dcc.Graph(figure=fig, id="map-graph"),
                html.Div(id="country-info", children="🖱️ Hover over a country or search above")
            ], style={"flex": "2", "padding": "10px"}),

            # Top & bottom 5 lists (right)
            html.Div([
                html.Div([
                    html.H3("🏆 Top 5", style={"textAlign": "center", "color": "#2e7d32"}),
                    html.Ul(
                        [html.Li(f"{row['country']} — {row[selected_metric]}") for _, row in top5.iterrows()],
                        style={"listStyleType": "none", "paddingLeft": "0"}
                    )
                ], style={"backgroundColor": "#e8f5e9", "border": "1px solid #c8e6c9", "borderRadius": "12px", "padding": "15px", "marginBottom": "20px"}),

                html.Div([
                    html.H3("⚠️ Bottom 5", style={"textAlign": "center", "color": "#c62828"}),
                    html.Ul(
                        [html.Li(f"{row['country']} — {row[selected_metric]}") for _, row in bottom5.iterrows()],
                        style={"listStyleType": "none", "paddingLeft": "0"}
                    )
                ], style={"backgroundColor": "#ffebee", "border": "1px solid #ffcdd2", "borderRadius": "12px", "padding": "15px"})
            ], style={"flex": "1", "padding": "10px"})
        ], style={"display": "flex", "flexDirection": "row", "alignItems": "flex-start"})
    ])


# Callback to update country info (depends on dropdown + active tab)
@app.callback(
    Output("country-info", "children"),
    Input("country-search", "value"),
    Input("metric-tabs", "value")
)
def update_country_info(selected_iso, selected_metric):
    if selected_iso:
        row = df[df["ISO"] == selected_iso].iloc[0]
        return f"📍 {row['country']} — {METRIC_LABELS[selected_metric]}: {row[selected_metric]}"
    return "🖱️ Hover over a country or search above"


if __name__ == "__main__":
    app.run(debug=True)
