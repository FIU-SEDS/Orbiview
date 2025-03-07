import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd
import time
import os

# Initialize Dash
app = dash.Dash(__name__)

# CSV file path
CSV_FILE_PATH = 'parsed_data.csv'

# Define rocket states
rocket_states = ["Idle", "Boost", "Apogee", "Drogue", "Main", "Landed"]

# Function to read the latest data from CSV
def read_latest_data():
    try:
        # Check if file exists
        if not os.path.exists(CSV_FILE_PATH):
            return None, None, None, None, None
            
        # Read the CSV file
        df = pd.read_csv(CSV_FILE_PATH)
        
        if df.empty:
            return None, None, None, None, None
            
        # Get the latest row
        latest = df.iloc[-1]
        
        # Extract values
        altitude = latest.get('Altitude', 0)
        acceleration = latest.get('Acceleration', 0)
        time_val = latest.get('Time', 0)
        rssi = latest.get('RSSI', 0)
        snr = latest.get('Signal-to-Noise', 0)
        
        return altitude, acceleration, time_val, rssi, snr
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None, None, None, None, None

# Function to determine rocket state based on altitude and acceleration
def determine_rocket_state(altitude, acceleration):
    # This is a simplistic model - you should adjust these thresholds
    # based on your actual rocket's flight profile
    if altitude < 0:
        return "Idle"
    elif acceleration > 150:
        return "Boost"
    elif altitude > 80:
        return "Apogee"
    elif altitude > 50:
        return "Drogue"
    elif altitude > 20:
        return "Main"
    else:
        return "Landed"

# Layout of the Dashboard
app.layout = html.Div([
    # Background video
    html.Video(
        src="/assets/rocket.mp4",
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

    # Vertical timeline and progress bar
    html.Div([
        # Text Labels
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

        # Progress Bar (Shifted right)
        html.Div([
            html.Div(id="progress-bar", style={
                'width': '10px', 'height': '10%', 'background-color': 'white',
                'transition': 'height 0.5s ease-in-out'
            })
        ], style={
            'width': '10px', 'height': '100%', 'display': 'flex', 'align-items': 'flex-end',
            'border': '2px solid white',
            'margin-left': '30px'  # Adjusted for spacing
        })
    ], style={
        'position': 'absolute', 'top': '4%', 'left': '10px', 'height': '80%',
        'display': 'flex', 'flex-direction': 'row', 'align-items': 'center'
    }),

    # Bottom telemetry data
    html.Div([
        html.Div([
            html.Div("ALTITUDE", style={'color': 'white', 'font-size': '14px'}),
            html.H3(id='altitude', style={'color': 'white'})
        ], style={'text-align': 'center', 'padding': '0 20px'}),
        html.Div([
            html.Div("ACCELERATION", style={'color': 'white', 'font-size': '14px'}),
            html.H3(id='acceleration', style={'color': 'white'})
        ], style={'text-align': 'center', 'padding': '0 20px'})
    ], style={
        'position': 'absolute', 'bottom': '20px', 'left': '60px',
        'display': 'flex', 'gap': '50px', 'background': 'rgba(0, 0, 0, 0.1)',
        'padding': '5px 20px', 'border-radius': '10px',
    }),

    # Mission time
    html.Div([
        html.H1("T+ 00:00:00", id='mission-time')
    ], style={
        'position': 'absolute', 'bottom': '20px', 'right': '20px',
        'background': 'rgba(0, 0, 0, 0.1)', 'padding': '10px 20px',
        'border-radius': '10px', 'color': 'white'
    }),



    # Logo
    html.Img(src="/assets/seds.png", style={'position': 'absolute', 'top': '10px', 'right': '10px', 'width': '100px', 'opacity': '0.5'}),

    # Interval component for real-time updates
    dcc.Interval(id='interval-component', interval=500, n_intervals=0)  # Check every 500ms
])

# Callback for updating progress bar and rocket state
@app.callback(
    dash.dependencies.Output('progress-bar', 'style'),
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_progress(n):
    # Read latest data
    altitude, acceleration, _, _, _ = read_latest_data()
    
    # If no data, keep at idle
    if altitude is None:
        current_state = "Idle"
    else:
        current_state = determine_rocket_state(altitude, acceleration)
    
    # Map states to progress percentages
    stage_progress = {
        "Idle": 100, "Boost": 85, "Apogee": 68, "Drogue": 51, "Main": 34, "Landed": 17
    }
    
    progress_height = stage_progress.get(current_state, 100)
    
    return {
        'width': '10px', 'height': f"{progress_height}%",
        'background-color': 'white', 'transition': 'height 0.5s ease-in-out'
    }

# Callback for updating telemetry data
@app.callback(
    [
        dash.dependencies.Output('altitude', 'children'),
        dash.dependencies.Output('acceleration', 'children'),
        dash.dependencies.Output('mission-time', 'children')
    ],
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_data(n):
    # Read latest data
    altitude, acceleration, time_val, _, _ = read_latest_data()
    
    # Format mission time
    if time_val is not None:
        minutes = int(time_val // 60)
        seconds = int(time_val % 60)
        centiseconds = int((time_val % 1) * 100)
        elapsed_time = f"T+ {minutes:02}:{seconds:02}:{centiseconds:02}"
    else:
        elapsed_time = "T+ 00:00:00"
    
    # Format altitude and acceleration
    altitude_str = f"{altitude:.2f} FT" if altitude is not None else "N/A"
    accel_str = f"{acceleration:.2f} G" if acceleration is not None else "N/A"
    
    return altitude_str, accel_str, elapsed_time

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)