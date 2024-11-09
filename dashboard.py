import dash
import dash_leaflet as dl
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import pandas as pd
import requests

# Load GeoJSON data for California counties
url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/california-counties.geojson'
response = requests.get(url)
california_geojson = response.json()

# Extract and sort county names for the dropdown
county_names = sorted([feature['properties']['name'] for feature in california_geojson['features']])

# Load fires data
fires_df = pd.read_csv('data_final/fires.csv')
fires_df['DATE'] = pd.to_datetime(fires_df['DATE'])

# Get the min and max dates for the slider
min_date = fires_df['DATE'].min()
max_date = fires_df['DATE'].max()

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.Div([
        dl.Map(center=[37.5, -119.5], zoom=6, children=[
            dl.TileLayer(),
            dl.GeoJSON(id='geojson', data=california_geojson),
            dl.LayerGroup(id='fire-markers')
        ], style={'width': '100%', 'height': '80vh'}, id='map'),
        dcc.RangeSlider(
            id='date-slider',
            min=min_date.timestamp(),
            max=max_date.timestamp(),
            value=[min_date.timestamp(), max_date.timestamp()],
            marks={int(min_date.timestamp()): min_date.strftime('%Y-%m-%d'),
                   int(max_date.timestamp()): max_date.strftime('%Y-%m-%d')},
            step=24*60*60,  # One day in seconds
            updatemode='mouseup'
        )
    ], style={'width': '50%', 'display': 'inline-block'}),
    html.Div([
        html.H1("Tones and E predicting FIRE", style={'textAlign': 'center'}),
        dcc.Dropdown(
            id='county-dropdown',
            options=[{'label': name, 'value': name} for name in county_names],
            placeholder="Select a county"
        )
    ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px'})
], style={'display': 'flex'})

# Helper function to flatten coordinates
def flatten_coordinates(coords):
    flat_coords = []
    for coord in coords:
        if isinstance(coord[0], list):
            flat_coords.extend(flatten_coordinates(coord))
        else:
            flat_coords.append(coord)
    return flat_coords

# Callback to update the GeoJSON layer and map center based on the selected county and date range
@app.callback(
    [Output('geojson', 'data'),
     Output('map', 'center'),
     Output('fire-markers', 'children')],
    [Input('county-dropdown', 'value'),
     Input('date-slider', 'value')]
)
def update_geojson(selected_county, date_range):
    start_date = pd.to_datetime(date_range[0], unit='s')
    end_date = pd.to_datetime(date_range[1], unit='s')

    if selected_county is None:
        geojson_data = california_geojson
        center = [37.5, -119.5]
    else:
        # Filter the GeoJSON data to only include the selected county
        filtered_features = [feature for feature in california_geojson['features']
                             if feature['properties']['name'] == selected_county]
        # Get the center of the selected county
        coordinates = flatten_coordinates(filtered_features[0]['geometry']['coordinates'])
        center = [sum(x[1] for x in coordinates) / len(coordinates), sum(x[0] for x in coordinates) / len(coordinates)]
        geojson_data = {'type': 'FeatureCollection', 'features': filtered_features}

    # Filter fire markers based on the selected date range
    filtered_fires = fires_df[(fires_df['DATE'] >= start_date) & (fires_df['DATE'] <= end_date)]
    fire_markers = [
        dl.Marker(position=[row['latitude'], row['longitude']])
        for _, row in filtered_fires.iterrows()
    ]

    return geojson_data, center, fire_markers

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)