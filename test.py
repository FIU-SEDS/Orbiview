import dash
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
        src="/assets/background.mp4",  # Use local video in the assets folder
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
            'object-fit': 'cover'  # Ensure the video fits well without being overly zoomed
        }
    ),
    
    # Top left telemetry data
    html.Div([
        html.Div([
            html.H4("TELEMETRY", style={'color': 'white', 'margin-bottom': '10px'}),
            html.Div([
                html.Div([
                    html.H6("SPEED", style={'color': 'white', 'margin-bottom': '5px'}),
                    html.H3(id='speed', style={'color': 'white'}),
                ], style={'padding': '0 20px', 'text-align': 'center'}),
                html.Div([
                    html.H6("ALTITUDE", style={'color': 'white', 'margin-bottom': '5px'}),
                    html.H3(id='altitude', style={'color': 'white'}),
                ], style={'padding': '0 20px', 'text-align': 'center'}),
            ])
        ], style={'margin-bottom': '20px'}),
        
        # Stage information below telemetry
        html.Div([
            html.H4("CURRENT STAGE", style={'color': 'white', 'margin-bottom': '10px'}),
            html.H3(id='rocket-stage', style={'color': 'white'}),
        ])
    ], style={
        'position': 'absolute', 'top': '0', 'left': '0',
        'background': 'rgba(0, 0, 0, 0.6)', 'padding': '20px',
        'border-radius': '10px', 'margin': '10px'
    }),

    # Bottom center elapsed mission time, positioned over the black bar
    html.Div([
        html.H1("T+ 00:00:02", id='mission-time', style={'color': 'white', 'font-size': '36px', 'margin-bottom': '0'})
    ], style={
        'position': 'absolute', 'bottom': '60px', 'left': '50%',
        'transform': 'translateX(-50%)', 'z-index': '2',  # Higher z-index to bring it to the front
        'text-align': 'center', 'background': 'rgba(0, 0, 0, 0.7)'
    }),

    # Rocket stage progress bar
    html.Div([
        html.Div("LAUNCH: FIU SEDS Sub-Scale", style={'color': 'white', 'font-weight': 'bold', 'font-size': '24px'}),
    ], style={
        'position': 'absolute', 'bottom': '0', 'left': '0', 'width': '100%',
        'padding': '10px', 'background': 'rgba(0, 0, 0, 0.7)', 'color': 'white',
        'text-align': 'center', 'height':'50px'  
    })
])

# Callback to update telemetry data and current stage
@app.callback(
    [
        dash.dependencies.Output('altitude', 'children'),
        dash.dependencies.Output('speed', 'children'),
        dash.dependencies.Output('rocket-stage', 'children'),
        dash.dependencies.Output('mission-time', 'children')
    ],
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_data(n):
    # Simulate new data for each update
    current_time = time.time() - start_time
    new_altitude = random.uniform(0, 100)  # Random altitude between 0 and 100
    new_speed = random.uniform(0, 50)  # Random speed between 0 and 50
    current_state = random.choice(rocket_states)
    elapsed_time = f"T+ {int(current_time // 60):02}:{int(current_time % 60):02}:{int((current_time % 1) * 100):02}"

    # Append new data to the lists
    times.append(current_time)
    altitudes.append(new_altitude)
    speeds.append(new_speed)

    return f"{new_altitude:.2f} km", f"{new_speed:.2f} km/h", current_state, elapsed_time

# Add the interval component for updating the data
app.layout.children.append(
    dcc.Interval(
        id='interval-component',
        interval=1000,  # in milliseconds
        n_intervals=0
    )
)

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
