import dash
import dash_leaflet as dl
from dash import dcc, html
import plotly.graph_objs as go
import random
import time

# Initialize Dash
app = dash.Dash(__name__)

# Global lists to store simulated data
times = []
altitudes = []
speeds = []
rocket_states = ["Idle", "Ascending", "Coasting", "Descending", "Landed"]

# Simulate some initial data for testing
start_time = time.time()
for i in range(20):
    current_time = time.time() - start_time
    altitude = random.uniform(0, 100)  # Random altitude value between 0 and 100
    speed = random.uniform(0, 50)  # Random speed between 0 and 50
    times.append(current_time)
    altitudes.append(altitude)
    speeds.append(speed)
    time.sleep(0.1)  # Simulate a small delay between measurements

# Layout of the Dashboard
app.layout = html.Div([
    # Background video
    html.Video(
        src="/assets/rocket.mp4",  # Use local video in the assets folder
        autoPlay=True,
        loop=True,
        muted=True,
        style={
            'position': 'fixed',
            'top': '50%',
            'left': '50%',
            'transform': 'translate(-50%, -50%)',
            'min-width': '100%',
            'min-height': '100%',
            'width': 'auto',
            'height': 'auto',
            'z-index': '-1',
            'object-fit': 'cover'
        }
    ),
    

    
    # Vertical timeline on the left
    html.Div([
        html.Div("INIT", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("IDLE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("BOOST", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("APOGEE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("DROGUE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("MAIN", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("LANDED", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'})
    ], style={
        'position': 'absolute', 'top': '4%', 'left': '10px',
        'height': '80%', 'display': 'flex', 'flex-direction': 'column',
        'justify-content': 'space-between', 'align-items': 'center',
        'font-size': '12px', 'font-weight': 'bold'
    }),

    # Bottom telemetry data
    html.Div([
        html.Div([
            html.Div("CAPSULE VELOCITY", style={'color': 'white', 'font-size': '14px'}),
            html.H3(id='speed', style={'color': 'white'})
        ], style={'text-align': 'center', 'padding': '0 20px'}),
        html.Div([
            html.Div("CAPSULE ALTITUDE", style={'color': 'white', 'font-size': '14px'}),
            html.H3(id='altitude', style={'color': 'white'})
        ], style={'text-align': 'center', 'padding': '0 20px'})
    ], style={
        'position': 'absolute', 'bottom': '20px', 'left': '15%',
        'transform': 'translateX(-50%)', 'display': 'flex',
        'gap': '50px', 'background': 'rgba(0, 0, 0, 0.1)',
        'padding': '5px 20px', 'border-radius': '10px', 
    }),

    # Bottom right mission time
    html.Div([
        html.H1("T+ 00:00:02", id='mission-time', style={'color': 'white', 'font-size': '30px'})
    ], style={
        'position': 'absolute', 'bottom': '20px', 'right': '20px',
        'background': 'rgba(0, 0, 0, 0.1)',
        'padding': '10px 20px', 'border-radius': '10px'
    }),
   
    html.Img(
    src="/assets/seds.png",  
    style={
        'position': 'absolute',
        'top': '10px',
        'right': '10px',
        'width': '100px',  
        'height': 'auto',
        'z-index': '10',
        'opacity': '0.5',
    }
),
])

@app.callback(
    [
        dash.dependencies.Output('altitude', 'children'),
        dash.dependencies.Output('speed', 'children'),
        dash.dependencies.Output('mission-time', 'children')
    ],
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_data(n):
    
    current_time = time.time() - start_time
    new_altitude = random.uniform(0, 100)  # Random altitude between 0 and 100
    new_speed = random.uniform(0, 50)  # Random speed between 0 and 50
    elapsed_time = f"T+ {int(current_time // 60):02}:{int(current_time % 60):02}:{int((current_time % 1) * 100):02}"

    # Append new data to the lists
    times.append(current_time)
    altitudes.append(new_altitude)
    speeds.append(new_speed)

    return f"{new_speed:.0f} MPH", f"{new_altitude:.0f} FT", elapsed_time


app.layout.children.append(
    dcc.Interval(
        id='interval-component',
        interval=1000,  # in milliseconds
        n_intervals=0
    )
)

# Run the Dash app
if __name__ == '__main__':
    # app.run_server(debug=True) # uncomment this if you need to debug to make the blue ball with debug features appear
    app.run_server(debug=False)