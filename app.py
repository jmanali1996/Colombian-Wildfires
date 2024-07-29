from dash import Dash, html, dcc, Input, Output, State
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd

# EDA
df = pd.read_parquet('https://raw.githubusercontent.com/jmanali1996/Colombian-Wildfires/main/Data/col_2000-2024.parquet')#, low_memory=False)
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
month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
df['month'] = df['month'].map(lambda x: month_order[x-1])
unique_months = sorted(df['month'].unique(), key=lambda x: month_order.index(x))
mo = [{'label':m,'value':m} for m in unique_months]
yo = [{'label':y,'value':y} for y in sorted(df['year'].unique())]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.UNITED])
app.layout = dbc.Container([
    html.H1("Wildfires in Colombia", style={'text-align': 'center'}),
    html.H5("The bar graph and map showcase the pattern of fire frequency and the spread of fires from 2000-2024", style={'text-align': 'center'}),
    html.Br(),
    html.Div([
    #checklists
        html.Div([
            html.Label(children=['Fire origin:'], style={'color': 'black', 'font-weight': 'bold'}),
            dcc.Checklist(
                id='fire_origin_type',
                options=df['fire origin'].unique(),
                value=[fo for fo in sorted(df['fire origin'].unique())],
                inline=True,
                labelStyle={'margin-right': 20}
            )
        ], style={'display': 'inline-block', 'width': '56%', 'margin-right': 20, 'vertical-align': 'top'}),
        html.Div([
            html.Label(children=['Fire time:'], style={'color': 'black', 'font-weight': 'bold'}),
            dcc.Checklist(
                id='fire_time_type',
                options=df['fire time'].unique(),
                value=[ft for ft in sorted(df['fire time'].unique())],
                inline=True,
                labelStyle={'margin-right': 20}
            )
        ], style={'display': 'inline-block', 'width': '40%', 'vertical-align': 'top'})
    ]),
    html.Br(),
    html.Div([
    #dropdowns
        html.Div([
            html.Label(children=['Month:'], style={'color': 'black', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id='month-variable',
                options=mo,
                value=None, 
                multi=True,
                searchable=True,
                placeholder="Select a month"
            ),
        ], style={'display': 'inline-block', 'width': '56%', 'margin-right': 20, 'vertical-align': 'top'}),
        html.Div([
            html.Label(children=['Year:'], style={'color': 'black', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id='year-variable',
                options=yo,
                value=None,
                multi=True,
                searchable=True,
                placeholder="Select a year"
            ),
        ], style={'display': 'inline-block', 'width': '40%', 'vertical-align': 'top'})
    ]),
    html.Br(),
    dbc.Button(id='fire-button', children="Submit", n_clicks=0),
    html.Br(),
    html.Br(),
    #fire instances count
    html.Div(id='count-output', style={'color': 'black', 'font-weight': 'bold'}),
    html.Br(),
    html.Div(id='placeholder', children="Select your preferences to view the bar graph and map"),
    dbc.Row([dbc.Col(dcc.Graph(id='bar'))]),
    dbc.Row([dbc.Col(dcc.Graph(id='map'))]),
], style={'margin-left': 10})

# COUNT, BAR GRAPH AND MAP CALLBACK
@app.callback(
    [Output('count-output', 'children'), 
    Output('bar', 'figure'),
    Output('map', 'figure'),
    Output('placeholder', 'children')],
    [Input('fire-button', 'n_clicks')],
    [State('fire_origin_type', 'value'),
    State('fire_time_type', 'value'),
    State('month-variable', 'value'),
    State('year-variable', 'value')],
    prevent_initial_call=True
)
def update_bar(n_clicks, selected_category, selected_value, selected_month, selected_year):
    if n_clicks > 0 and selected_category and selected_value and selected_month and selected_year:
        df_sub = df[(df['fire origin'].isin(selected_category)) & (df['fire time'].isin(selected_value)) & (df['month'].isin(selected_month)) & (df['year'].isin(selected_year))]
        count = df_sub.shape[0]
        df_sub_bar = df_sub.groupby(["date","fire origin"])["brightness"].mean().reset_index()
        fig_bar = px.bar(
            df_sub_bar,
            x="date",
            y="brightness",
            labels={"brightness": "fire temperature (K)"},
            color="fire origin",
            barmode='group',
            width=1400,
            height=700
        )
        fig_bar.update_layout(
            legend=dict(
                orientation='h',  
                yanchor='bottom',
                y=1.02,  
                xanchor='right',
                x=1
            )
        )
        fig_map = px.density_mapbox(
            df_sub,
            lat="latitude",
            lon="longitude",
            hover_data={"latitude": False, "longitude": False, "date": False},
            z="brightness",
            labels={"brightness": "fire temperature (K)"},
            animation_frame="date",
            mapbox_style="carto-darkmatter",
            zoom=5,
            width=1400,
            height=700
        )
        return f"Fire instances: {count}", fig_bar, fig_map, ''
    else:
        return {}, {}, {}, {}

if __name__ == '__main__':
    app.run_server(debug=True)
