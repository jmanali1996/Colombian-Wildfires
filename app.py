from dash import Dash, html, dcc, Input, Output, State
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# Load historic wildlife data and make necessary changes
df = pd.read_parquet('https://raw.githubusercontent.com/jmanali1996/Colombian-Wildfires/main/Data/col_2000-2024.parquet')
df['type'] = df['type'].fillna(df['type'].mode()[0])
df = df.astype({"type": 'str'})
df.loc[df['type'] == '0.0', 'type'] = "Presumed vegetation fire"
df.loc[df['type'] == '1.0', 'type'] = "Active volcano"
df.loc[df['type'] == '2.0', 'type'] = "Other static land source"
df.loc[df['type'] == '3.0', 'type'] = "Offshore"
df['acq_date'] = pd.to_datetime(df.acq_date, format='%Y-%m-%d')
df['year'] = df['acq_date'].dt.year
df['month'] = df['acq_date'].dt.month
df = df.astype({"acq_date": 'str', "daynight": 'str'})
df.loc[df['daynight'] == 'D', 'daynight'] = "Day time fire"
df.loc[df['daynight'] == 'N', 'daynight'] = "Night time fire"
df = df.rename(columns={"type": "fire origin", "acq_date": "date", "daynight": "fire time"})

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.layout = dbc.Container([
    html.H1("Wildfires in Colombia", style={'text-align': 'center'}),
    html.H5("The line graph and map showcase the pattern of fire frequency and the spread of fires from 2000-2024", style={'text-align': 'center'}),
    html.H6("Kindly use the filters to get the desired insights."),
    # Fire origin checklist
    html.Label(children=['Fire origin:'], style={'color': 'white', 'font-weight': 'bold'}),
    dcc.Checklist(
        id='fire_origin_type',
        options=df['fire origin'].unique(),
        value=[fo for fo in sorted(df['fire origin'].unique())],
        inline=True,
        labelStyle={'margin-right': 20}
    ),
    html.Br(),
    # Fire time checklist
    html.Label(children=['Fire time:'], style={'color': 'white', 'font-weight': 'bold'}),
    dcc.Checklist(
        id='fire_time_type',
        options=df['fire time'].unique(),
        value=[ft for ft in sorted(df['fire time'].unique())],
        inline=True,
        labelStyle={'margin-right': 20}
    ),
    html.Br(),
    # Months dropdown
    html.Div([
        html.Label(children=['Month:'], style={'color': 'white', 'font-weight': 'bold'}),
        dcc.Dropdown(
            id='month-variable',
            options=[{'label':m,'value':m} for m in sorted(df['month'].unique())],
            value=None,
            multi=True,
            searchable=True,
            placeholder="Select a month"
        ),
    ], style={'display': 'inline-block', 'margin-right': 20, 'width': 300}),
    # Years dropdown
    html.Div([
        html.Label(children=['Year:'], style={'color': 'white', 'font-weight': 'bold'}),
        dcc.Dropdown(
            id='year-variable',
            options=[{'label':y,'value':y} for y in sorted(df['year'].unique())],
            value=None,
            multi=True,
            searchable=True,
            placeholder="Select a year"
        ),
    ], style={'display': 'inline-block', 'margin-right': 20, 'width': 300}),
    html.Br(),
    html.Br(),
    # Map theme checklist
    html.Label(children=['Map theme:'], style={'color':'white', 'font-weight': 'bold'}),
    dcc.RadioItems(
        id='map-theme',
        options=[
            {'label': 'Light Theme', 'value': 'light'},
            {'label': 'Dark Theme', 'value': 'dark'}
        ],
        value='light',  
        inline=True,
        labelStyle={'margin-right': 20}
    ),
    html.Br(),
    dbc.Button(id='fire-button', children="Submit"),
    html.Br(),
    html.Br(),
    # Fire instances count
    html.Div(id='count-output', style={'color': 'white', 'font-weight': 'bold'}),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(dcc.Graph(id='line'))
        ]
    ),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(dcc.Graph(id='graph'))
        ]
    ),

], style={'margin-left': 20})


# Getting count and line chart
@app.callback(
    Output('count-output', 'children'),
    Output('line', 'figure'),
    Input('fire-button', 'n_clicks'),
    State('fire_origin_type', 'value'),
    State('fire_time_type', 'value'),
    State('month-variable', 'value'),
    State('year-variable', 'value'),
    prevent_initial_call=True
)
def update_line(_, selected_category, selected_value, selected_month, selected_year):
    if selected_month and selected_year:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value)) & (df['month'].isin(selected_month)) & (df['year'].isin(selected_year))]
    else:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value))]
    count = df_sub.shape[0]
    df_sub = df_sub.groupby(["date","fire origin"])["brightness"].mean().reset_index()
    print(df_sub)
    fig_line = px.bar(
        df_sub,
        x="date",
        y="brightness",
        labels={"brightness": "fire temperature (K)"},
        color="fire origin",
        barmode='group',
        title=f"Line Chart for {selected_month} {selected_year}",
        width=1400,
        height=700
        )
    return f"Fire instances: {count}", fig_line

# Getting map
@app.callback(
    Output('graph', 'figure'),
    Input('fire-button', 'n_clicks'),
    State('fire_origin_type', 'value'),
    State('fire_time_type', 'value'),
    State('map-theme', 'value'),
    State('month-variable', 'value'),
    State('year-variable', 'value'),
    prevent_initial_call=True
)
def update_map(_, selected_category, selected_value, map_theme, selected_month, selected_year):
    if selected_month and selected_year:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value)) & (df['month'].isin(selected_month)) & (df['year'].isin(selected_year))]
    else:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value))]
    print(len(df_sub))
    fig_map = px.scatter_mapbox(
        df_sub,
        lat="latitude",
        lon="longitude",
        hover_data={"latitude": False, "longitude": False, "date": False},
        color="brightness",
        labels={"brightness": "fire temperature (K)"},
        animation_frame="date",
        mapbox_style=map_theme,
        zoom=5,
        title=f"Map for {selected_month} {selected_year}",
        width=1400,
        height=700
        )
    fig_map.update_layout(title=f'Map for {selected_month} {selected_year}')
    return fig_map

if __name__ == '__main__':
    app.run_server(debug=True)
