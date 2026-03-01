import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np

# -------------------------------------------------
# Dummy dataset (replace this with your dataframe)
# -------------------------------------------------
np.random.seed(0)

dims = {
    "dim1": np.arange(1, 11),           # X axis
    "dim2": [16, 32, 64],
    "dim3": [1, 2, 4],
    "dim4": [128, 256],
    "dim5": [0, 1],
    "dim6": [10, 20, 30]
}

records = []
for d1 in dims["dim1"]:
    for d2 in dims["dim2"]:
        for d3 in dims["dim3"]:
            for d4 in dims["dim4"]:
                for d5 in dims["dim5"]:
                    for d6 in dims["dim6"]:
                        value = d1 * d3 + d2/10 + d4/50 + d5*2 + d6/5
                        records.append({
                            "dim1": d1,
                            "dim2": d2,
                            "dim3": d3,
                            "dim4": d4,
                            "dim5": d5,
                            "dim6": d6,
                            "value": value
                        })

df = pd.DataFrame(records)

# -------------------------------------------------
# Dash App
# -------------------------------------------------
app = dash.Dash(__name__)

slider_dims = ["dim2", "dim3", "dim4", "dim5", "dim6"]

app.layout = html.Div([
    html.H2("Interactive 2D Plot"),

    dcc.Graph(id="main-plot"),

    html.Div([
        html.Div([
            html.Label(dim),
            dcc.Slider(
                id=f"{dim}-slider",
                min=min(df[dim]),
                max=max(df[dim]),
                step=None,
                value=min(df[dim]),
                marks={int(v): str(v) for v in sorted(df[dim].unique())}
            )
        ], style={"margin": "20px"})
        for dim in slider_dims
    ])
])


# -------------------------------------------------
# Callback: Update Plot
# -------------------------------------------------
@app.callback(
    Output("main-plot", "figure"),
    [Input(f"{dim}-slider", "value") for dim in slider_dims]
)
def update_plot(*slider_values):

    filtered_df = df.copy()

    for dim, val in zip(slider_dims, slider_values):
        filtered_df = filtered_df[filtered_df[dim] == val]

    fig = px.line(
        filtered_df,
        x="dim1",
        y="value",
        markers=True
    )

    fig.update_layout(
        height=600,
        template="plotly_white"
    )

    return fig


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)
