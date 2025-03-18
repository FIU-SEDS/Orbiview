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
rocket_states = ["INIT","Idle", "Boost", "Apogee", "Drogue", "Main", "Landed"]

# Function to read the latest data from CSV
def read_latest_data():
    try:
        # Check if file exists
        if not os.path.exists(CSV_FILE_PATH):
            return None, None, None, None, None, None, None, None, None, None
            
        # Read the CSV file
        df = pd.read_csv(CSV_FILE_PATH)
        
        if df.empty:
            return None, None, None, None, None, None, None, None, None, None
            
        # Get the latest row
        latest = df.iloc[-1]
        
        # Extract values based on your CSV columns
        accel_x = latest.get('acceleration_x', 0)
        accel_y = latest.get('acceleration_y', 0)
        accel_z = latest.get('acceleration_z', 0)
        gyro_x = latest.get('gyro_x', 0)
        gyro_y = latest.get('gyro_y', 0)
        gyro_z = latest.get('gyro_z', 0)
        time_val = latest.get('time_elapsed', 0)
        state = latest.get('rocket_state', 1)
        rssi = latest.get('rssi', 0)
        snr = latest.get('signal_to_noise', 0)
        
        return accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, time_val, state, rssi, snr
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None, None, None, None, None, None, None, None, None, None

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
            html.Div("LANDED", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("MAIN", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("DROGUE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("APOGEE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("BOOST", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("IDLE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("INIT", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'})
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

        html.Div(style={'border-left': '3px solid white', 'height': '70px'}),
            

        html.Div([
            html.Div("ACCELERATION", style={'color': 'white', 'font-size': '14px'}),
            html.H3(id='acceleration', style={'color': 'white'})
        ], style={'text-align': 'center', 'padding': '0 20px'})
    ], style={
        'position': 'absolute', 'bottom': '20px', 'left': '60px',
        'display': 'flex', 'gap': '50px',
        'padding': '5px 100px', 'border-radius': '10px',
    }),

    # Mission time
    html.Div([
        html.H1("T+ 00:00:00", id='mission-time')
    ], style={
        'position': 'absolute', 'bottom': '20px', 'right': '20px',
        'padding': '10px 20px',
        'border-radius': '10px', 'color': 'white','font-size': '24px',
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
    _, _, _, _, _, _, _, state, _, _ = read_latest_data()
    
    # If no data, use default
    if state is None:
        state = 1  # Default to first state
    
    # Map states to progress percentages
    stage_progress = {
        7: 100, 6: 84, 5: 70, 4: 56, 3: 42, 2: 28, 1: 17
    }
    
    progress_height = stage_progress.get(state, 17)
    
    return {
        'width': '10px', 'height': f"{progress_height}%",
        'background-color': 'white', 'transition': 'height 0.5s ease-in-out'
    }

def update_data(n):
    # Read latest data
    accel_x, _, _, _, _, _, time_val, _, _, _ = read_latest_data()
    
    # We don't have altitude in this CSV structure
    # You might need to calculate it or find another way to get it
    altitude = 0  # Or set to None if you prefer
    
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
    accel_str = f"{accel_x:.2f} G" if accel_x is not None else "N/A"
    
    return altitude_str, accel_str, elapsed_time

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)