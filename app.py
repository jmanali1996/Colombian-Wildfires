from dash import Dash, html, dcc, Input, Output
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# Load historic wildfile data and make necessary changes
df = pd.read_parquet('https://raw.githubusercontent.com/jmanali1996/Colombian-Wildfires/main/Data/col_2000-2024.parquet')
df['type'] = df['type'].fillna(df['type'].mode()[0])
df['acq_date'] = pd.to_datetime(df.acq_date, format='%Y-%m-%d')
df = df.astype({"type": 'int'})
df['year'] = df['acq_date'].dt.year
df['month'] = df['acq_date'].dt.month
df = df.astype({"acq_date": 'str'})
df = df.rename(columns={"type": "fire origin", "acq_date": "date", "daynight": "fire time"})

# Custom labels and order for the nature checklist options
fo_custom_labels = {
    0: 'Presumed vegetation fire (0)',
    1: 'Active volcano (1)',
    2: 'Other static land source (2)',
    3: 'Offshore (3)'
}
custom_order = ['0', '1', '2', '3']

# Custom labels for the fire time checklist options
ft_custom_labels = {
    'D': 'Day time fire (D)',
    'N': 'Night time fire (N)'
}

app = dash.Dash(__name__)
app.layout = dbc.Container([
    html.H1("Wildfires in Colombia", style={'text-align': 'center'}),
    html.H2("The line graph and map showcase the pattern of fire frequency and the spread of fires from 2000-2024", style={'text-align': 'center'}),
    html.H3("Kindly use the filters to get the desired insights."),
    # Fire origin checklist
    html.Label(children=['Fire origin:'], style={'color':'black', 'font-weight': 'bold'}),
    dcc.Checklist(
        id='fire_origin_type',
        options=[{'label':fo_custom_labels[fo],'value':fo} for fo in sorted(df['fire origin'].unique())],
        value=[fo for fo in sorted(df['fire origin'].unique())],
        inline=True,
        labelStyle={'margin-right': 20}
    ),
    html.Br(),
    # Fire time checklist
    html.Label(children=['Fire time:'], style={'color':'black', 'font-weight': 'bold'}),
    dcc.Checklist(
        id='fire_time_type',
        options=[{'label':ft_custom_labels[ft],'value':ft} for ft in sorted(df['fire time'].unique())],
        value=[ft for ft in sorted(df['fire time'].unique())],
        inline=True,
        labelStyle={'margin-right': 20}
    ),
    html.Br(),
    # Months dropdown
    html.Div([
        html.Label(children=['Month:'], style={'color':'black', 'font-weight': 'bold'}),
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
        html.Label(children=['Year:'], style={'color':'black', 'font-weight': 'bold'}),
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
    html.Label(children=['Map theme:'], style={'color':'black', 'font-weight': 'bold'}),
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
    # Fire instances count
    html.Div(id='count-output', style={'color':'black', 'font-weight': 'bold'}),
    html.Div(
        [dbc.Row(
            [
                dbc.Col(html.Div(dcc.Graph(id='line')), md=4),
                dbc.Col(html.Div(dcc.Graph(id='graph')), md=4)
            ]
            ),
        ]
    )
])

# Getting count
@app.callback(
    Output('count-output', 'children'),
    [Input('fire_origin_type', 'value'),
    Input('fire_time_type', 'value'),
    Input('month-variable', 'value'),
    Input('year-variable', 'value')]
)
def update_count(selected_category, selected_value, selected_month, selected_year):
    if selected_month and selected_year:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value)) & (df['month'].isin(selected_month)) & (df['year'].isin(selected_year))]
    else:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value))]
    count = df_sub.shape[0]
    return f"Fire instances: {count}"

# Getting line chart
@app.callback(
    Output('line', 'figure'),
    [Input('fire_origin_type', 'value'),
    Input('fire_time_type', 'value'),
    Input('month-variable', 'value'),
    Input('year-variable', 'value')]
)
def update_line(selected_category, selected_value, selected_month, selected_year):
    if selected_month and selected_year:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value)) & (df['month'].isin(selected_month)) & (df['year'].isin(selected_year))]
    else:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value))]
    fig_line = px.line(
        df_sub,
        x="date",
        y="brightness",
        labels={"brightness": "fire temperature (K)"},
        color="fire origin",
        category_orders={'fire origin': custom_order},
        hover_data={"fire time": True},
        title=f"Line Chart for {selected_month} {selected_year}",
        width=1400,
        height=700
        )
    return fig_line

# Getting map
@app.callback(
    Output('graph', 'figure'),
    [Input('fire_origin_type', 'value'),
    Input('fire_time_type', 'value'),
    Input('map-theme', 'value'),
    Input('month-variable', 'value'),
    Input('year-variable', 'value')]
)
def update_map(selected_category, selected_value, map_theme, selected_month, selected_year):
    if selected_month and selected_year:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value)) & (df['month'].isin(selected_month)) & (df['year'].isin(selected_year))]
    else:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value))]
    fig_map = px.scatter_mapbox(
        df_sub,
        lat="latitude" ,
        lon="longitude",
        hover_data={"latitude":False, "longitude":False, "date": False},
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
