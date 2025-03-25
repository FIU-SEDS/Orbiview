import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd
import time
import os
import cv2
from flask import Response, Flask
import numpy as np
import math

# Initialize Flask server
server = Flask(__name__)

# Initialize Dash
app = dash.Dash(__name__, server=server)

# CSV file path
CSV_FILE_PATH = 'parsed_data.csv'

# Define rocket states
rocket_states = ["INIT", "Idle", "Boost", "Apogee", "Drogue", "Main", "Landed"]

# Function to read the latest data from CSV
def read_latest_data():
    try:
        # Read actual data from CSV
        df = pd.read_csv(CSV_FILE_PATH)
        latest_row = df.iloc[-1]
        
        return (
            latest_row['accel_x'], 
            latest_row['accel_y'], 
            latest_row['accel_z'], 
            latest_row['gyro_x'], 
            latest_row['gyro_y'], 
            latest_row['gyro_z'], 
            latest_row['time'], 
            latest_row['state'], 
            latest_row['rssi'], 
            latest_row['snr']
        )
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None, None, None, None, None, None, None, None, None, None

def generate_frames():
    while True:
        camera = cv2.VideoCapture(0)  # Use the first webcam

        if not camera.isOpened():
            print("Error: Could not open video device")
            time.sleep(1)  # Wait before retrying
            continue

        try:
            while True:
                success, frame = camera.read()
                if not success:
                    break
                else:
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_bytes = buffer.tobytes()

                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            camera.release()

def calculate_tilt(acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z):
    # Handle None values
    acc_x = acc_x if acc_x is not None else 0
    acc_y = acc_y if acc_y is not None else 0
    acc_z = acc_z if acc_z is not None else 0
    gyro_x = gyro_x if gyro_x is not None else 0
    gyro_y = gyro_y if gyro_y is not None else 0
    gyro_z = gyro_z if gyro_z is not None else 0

    # Use gyroscope data more directly for rotation
    # Combine rotations from different axes
    tilt_x = gyro_x  # Rotation around X-axis
    tilt_y = gyro_y  # Rotation around Y-axis
    
    # Calculate combined tilt angle using both x and y rotations
    combined_tilt = math.atan2(tilt_y, tilt_x)
    tilt_deg = math.degrees(combined_tilt)

    return tilt_deg

# Flask route to serve the video feed
@server.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Layout of the Dashboard
app.layout = html.Div([
    # Background video
    html.Img(
        src="/video_feed",
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

    html.Div(
        style={
            'position': 'absolute',
            'bottom': '50px',  # Adjust this to move it vertically
            'left': '50%',     # Center it horizontally
            'transform': 'translateX(-50%)',  # Ensure exact center
            'width': '5px',    # Make it very narrow
            'height': '1px',   # Keep it thin
            'backgroundColor': 'white',  # Make it visible
            'zIndex': '10'
        }
    ),

    # Gyroscope tilt container
    html.Div([
        # Horizontal line for 180 degree refeerence
        html.Div(
            style={
                'position': 'absolute',
                'top': '73%',
                'left': '625px',
                'width': '225px',
                'height': '1px',
                'borderTop': '4px dotted rgba(255,255,255,0.8)',
                'zIndex': '10'
            }
        ),
        
        # Tilt line
        html.Div(
            id='tilt-line',
            style={
                'position': 'absolute',
                'bottom': '50px',
                'left': '50%',
                'transform': 'translateX(-50%)',
                'width': '5px',
                'height': '100px',
                'background-color': 'white',
                'transformOrigin': 'center bottom',
                'transition': 'transform 0.1s linear',
                'zIndex': '20'
            }
        )
    ], style={
        'position': 'absolute',
        'width': '100%',
        'height': '200px',
        'bottom': '0',
        'left': '0'
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

@app.callback(
    dash.dependencies.Output('altitude', 'children'),
    dash.dependencies.Output('acceleration', 'children'),
    dash.dependencies.Output('mission-time', 'children'),
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
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

@app.callback(
    dash.dependencies.Output('tilt-line', 'style'),
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_tilt_line(n):
    # Read latest data
    accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, _, _, _, _ = read_latest_data()
    
    # Calculate tilt angle
    tilt_value = calculate_tilt(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)

    return {
        'position': 'absolute',
        'bottom': '50px',
        'left': '50%',
        'transform': f'translateX(-50%) rotate({tilt_value}deg)',
        'width': '5px',
        'height': '100px',
        'background-color': 'white',
        'transform-origin': 'center bottom',
        'transition': 'transform 0.1s linear',
        'z-index': '20'
    }

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=False)