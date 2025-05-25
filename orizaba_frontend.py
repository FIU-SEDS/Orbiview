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
import glob

# Initialize Flask server
server = Flask(__name__)

# Initialize Dash
app = dash.Dash(__name__, server=server)

# Flight logs directory
LOGS_DIR = "Flight_Logs"

# Define rocket states
rocket_states = ["INIT", "Idle", "Boost", "Burnout", "Coast", "Apogee", "Descent_Drogue", "Descent_Main", "Landed"]

# Last file check time and current file
last_file_check = 0
current_file = None
last_read_line = 0

# Function to find the most recent CSV file in the logs directory
def find_latest_csv():
    global current_file, last_file_check
    
    # Only check for a new file every 5 seconds to avoid excessive file system operations
    current_time = time.time()
    if current_time - last_file_check < 5 and current_file is not None:
        return current_file
    
    # Update the last check time
    last_file_check = current_time
    
    try:
        # Get all CSV files in the logs directory
        files = glob.glob(os.path.join(LOGS_DIR, "Flight_Data_*.csv"))
        
        if not files:
            print("No CSV files found in the logs directory.")
            return None
        
        # Sort files by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Get the most recent file
        latest_file = files[0]
        
        # Check if the file has changed
        if latest_file != current_file:
            print(f"New log file detected: {latest_file}")
            current_file = latest_file
            # Reset line counter when switching to a new file
            global last_read_line
            last_read_line = 0
        
        return latest_file
    
    except Exception as e:
        print(f"Error finding latest CSV file: {e}")
        return None

# Function to read the latest data from CSV
def read_latest_data():
    csv_file = find_latest_csv()
    
    if csv_file is None:
        return None, None, None, None, None, None, None, None, None, None
    
    try:
        # Read actual data from CSV
        df = pd.read_csv(csv_file)
        
        # Check if there are new lines to read
        global last_read_line
        if len(df) <= last_read_line:
            # No new data
            if last_read_line > 0:
                # Return the last known data
                latest_row = df.iloc[last_read_line - 1]
            else:
                # No data yet
                return None, None, None, None, None, None, None, None, None, None
        else:
            # New data available
            latest_row = df.iloc[-1]
            last_read_line = len(df)
        
        return (
            latest_row['acceleration_x'],
            latest_row['acceleration_y'],
            latest_row['acceleration_z'],
            latest_row['gyro_x'], 
            latest_row['gyro_y'], 
            latest_row['gyro_z'], 
            latest_row['time_elapsed'],
            latest_row['rocket_state'],
            latest_row['rssi'], 
            latest_row['signal_to_noise']
        )
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None, None, None, None, None, None, None, None, None, None

def generate_frames():
    while True:
        camera = cv2.VideoCapture(0)  # Use the first webcam

        # Error troubleshooting
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
            html.Div("DESCENT_MAIN", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("DESCENT_DROGUE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("APOGEE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
             html.Div("COAST", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
             html.Div("BURNOUT", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("BOOST", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("IDLE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
            html.Div("INIT", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'})
        ], style={
            'position': 'absolute', 'top': '4%', 'left': '10px',
            'height': '80%', 'display': 'flex', 'flex-direction': 'column',
            'justify-content': 'space-between', 'align-items': 'center',
            'font-size': '8px', 'font-weight': 'bold'
        }),

        # Progress Bar (Shifted right)
        html.Div([
            html.Div(id="progress-bar", style={
                'width': '8px', 'height': '10%', 'background-color': 'white',
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

    # Bottom screen shadow 
    html.Div(
        children=[
            html.Div(
                style={
                    "position": "absolute",
                    "width": "100%",  # Ensure it covers the full width of the viewport
                    "height": "20vh",  # Use viewport height for responsiveness
                    "background": "linear-gradient(to bottom, transparent, rgba(0, 0, 0, 1))",  # Smooth gradient
                    "bottom": "0",  # Stick to the bottom of the viewport
                    "left": "0",  # Align to the left edge
                }
            )
        ],
        style={
            "position": "relative",
            "height": "100vh",  # Ensure it spans the full viewport height
            "display": "flex",
            "flex-direction": "column",
        }
    ),

    # Bottom telemetry data
    html.Div([
        html.Div([
            html.Div("ALTITUDE", style={'color': 'white', 'font-size': '14px'}),
            html.H3(id='altitude', style={'color': 'white'})
        ], style={'text-align': 'center', 'padding': '0 20px'}),

        html.Div(style={'border-left': '3px solid white', 'height': '70px'}),
            
        html.Div([
            html.Div("VELOCITY(MPH)", style={'color': 'white', 'font-size': '14px'}),
            html.H3(id='velocity(mph)', style={'color': 'white'})
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
        # Horizontal line for 180 degree reference 
        # Might be modified to be a circle or include degrees 
        html.Div(
            style={
                'position': 'relative',
                'top': '73%',
                'left': '625px',
                'width': '225px',
                'height': '1px',
                'borderTop': '4px dotted rgba(255,255,255,0.8)',
                'zIndex': '10'
            }
        ),
        
        # Tilt line (gyroscope)
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
    
    progress_height = stage_progress.get(int(state), 17)
    
    return {
        'width': '10px', 'height': f"{progress_height}%",
        'background-color': 'white', 'transition': 'height 0.5s ease-in-out'
    }

@app.callback(
    dash.dependencies.Output('altitude', 'children'),
    dash.dependencies.Output('velocity', 'children'),
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
        minutes = int((time_val // 4) // 60)
        seconds = int((time_val // 4) % 60)
        centiseconds = int((time_val % 1) * 100)
        elapsed_time = f"T+ {minutes:02}:{seconds:02}:{centiseconds:02}"
    else:
        elapsed_time = "T+ 00:00:00"
    
    # Format altitude and velocity
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
    # Create logs directory if it doesn't exist
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Initial check for the latest CSV file
    find_latest_csv()
    
    # Run the Dash app
    app.run(debug=False)  # Removed blue debug icon on bottom right