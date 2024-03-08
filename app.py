from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd

# Load historic wildfile data ---------------------------------------------
df = pd.read_csv('https://raw.githubusercontent.com/oferreirap/wildfires_data_app/main/Data/modis_2022_Colombia.csv')
df = df[(df["acq_date"] > "2022-01-31") & (df["acq_date"] < "2022-03-01")]  # limit fires to the month of February

app = Dash()
app.layout = html.Div([
    html.H1("Fires in Colombia - February 2022"),
    dcc.Graph(figure=px.scatter_mapbox(df,
              lat="latitude" ,
              lon="longitude",
              hover_data={"latitude":False, 'longitude':False, 'acq_date': False},
              color="brightness",
              animation_frame="acq_date",
              mapbox_style='carto-darkmatter',
              zoom=5).update_layout(margin={"r":0,"t":0,"l":0,"b":0}),
              style={'height':'700px', 'width':'1400px'}
    )
])

app.run_server()
