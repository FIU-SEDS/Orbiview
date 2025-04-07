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
import serial
import threading
from queue import Queue
import csv

# Initialize Flask server
server = Flask(__name__)

# Initialize Dash
app = dash.Dash(__name__, server=server)

# Serial port configuration - change COM13 to your port
SERIAL_PORT = 'COM13'  # Use '/dev/ttyUSB0' for Linux
BAUDRATE = 115200

# Define rocket states
rocket_states = ["INIT", "Idle", "Boost", "Apogee", "Drogue", "Main", "Landed"]

# Queue for sharing data between threads
data_queue = Queue(maxsize=1)

# Current data storage
current_data = {
    'acceleration_x': 0,
    'acceleration_y': 0,
    'acceleration_z': 0,
    'gyro_x': 0,
    'gyro_y': 0,
    'gyro_z': 0,
    'time_elapsed': 0,
    'rocket_state': 1,
    'rssi': 0,
    'signal_to_noise': 0
}

# Flag to track if connection is active
is_connected = False

# Set up CSV logging
output_dir = "Flight_Logs"
os.makedirs(output_dir, exist_ok=True)
current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
output_csv = os.path.join(output_dir, f"Flight_Data_{current_time}.csv")

# Initialize CSV file
with open(output_csv, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["acceleration_x", "acceleration_y", "acceleration_z", 
                   "gyro_x", "gyro_y", "gyro_z", 
                   "time_elapsed", "rocket_state", "rssi", "signal_to_noise"])

print(f"Data will be saved to: {output_csv}")

# Serial reader thread function
def serial_reader():
    global is_connected
    ser = None
    reconnect_delay = 2  # seconds
    
    while True:
        # Try to connect if not connected
        if not is_connected:
            try:
                # Close previous connection if exists
                if ser is not None:
                    ser.close()
                
                # Open new serial connection
                ser = serial.Serial(port=SERIAL_PORT, baudrate=BAUDRATE, timeout=1)
                time.sleep(reconnect_delay)  # Allow time for connection to establish
                is_connected = True
                print(f"Connected to {SERIAL_PORT}. Waiting for data...")
            except Exception as e:
                print(f"Connection failed: {e}. Retrying in {reconnect_delay} seconds...")
                time.sleep(reconnect_delay)
                continue
        
        # Read data if connected
        try:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()  # Read and decode serial data
                if "+RCV=" in line:
                    clean_data = line.replace("+RCV=", "")  # For old code it is Received: Recieved+RCV=
                    data_values = clean_data.split(',')
                    
                    # Parse data values
                    if len(data_values) >= 12:  # Ensure we have all expected values
                        parsed_data = {
                            'acceleration_x': int(data_values[2]),
                            'acceleration_y': int(data_values[3]),
                            'acceleration_z': int(data_values[4]),
                            'gyro_x': int(data_values[5]),
                            'gyro_y': int(data_values[6]),
                            'gyro_z': int(data_values[7]),
                            'time_elapsed': int(data_values[8]),
                            'rocket_state': int(data_values[9]),
                            'rssi': int(data_values[10]),
                            'signal_to_noise': float(data_values[11])
                        }
                        
                        # Save to CSV
                        with open(output_csv, mode='a', newline='') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow([
                                parsed_data['acceleration_x'], 
                                parsed_data['acceleration_y'], 
                                parsed_data['acceleration_z'],
                                parsed_data['gyro_x'], 
                                parsed_data['gyro_y'], 
                                parsed_data['gyro_z'],
                                parsed_data['time_elapsed'], 
                                parsed_data['rocket_state'], 
                                parsed_data['rssi'], 
                                parsed_data['signal_to_noise']
                            ])
                        
                        # Update current data with new values
                        # If queue is full, replace the old data
                        if data_queue.full():
                            try:
                                data_queue.get_nowait()
                            except:
                                pass
                        data_queue.put(parsed_data)
            
            time.sleep(0.05)  # Small delay to prevent CPU hogging
            
        except serial.SerialException as e:
            print(f"Serial connection lost: {e}. Attempting to reconnect...")
            is_connected = False
            time.sleep(reconnect_delay)
        except Exception as e:
            print(f"Error reading data: {e}")
            time.sleep(0.5)  # Brief pause before trying again
    
    # Clean up
    if ser is not None:
        ser.close()

# Function to read the latest data
def read_latest_data():
    global current_data
    
    # Try to get new data from queue
    try:
        if not data_queue.empty():
            current_data = data_queue.get_nowait()
    except:
        pass  # Use the last known data if can't get new data
    
    # Return the current data values
    return (
        current_data['acceleration_x'],
        current_data['acceleration_y'],
        current_data['acceleration_z'],
        current_data['gyro_x'],
        current_data['gyro_y'],
        current_data['gyro_z'],
        current_data['time_elapsed'],
        current_data['rocket_state'],
        current_data['rssi'],
        current_data['signal_to_noise']
    )

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
            html.Div("ACCELERATION", style={'color': 'white', 'font-size': '14px'}),
            html.H3(id='acceleration', style={'color': 'white'})
        ], style={'text-align': 'center', 'padding': '0 20px'})
    ], style={
        'position': 'absolute', 'bottom': '20px', 'left': '60px',
        'display': 'flex', 'gap': '50px',
        'padding': '5px 100px', 'border-radius': '10px',
    }),

    # Connection status (new element)
    html.Div([
        html.H3(id='connection-status', style={'color': 'white'})
    ], style={
        'position': 'absolute', 'top': '20px', 'left': '20px',
        'padding': '5px 15px', 'border-radius': '5px', 
        'background-color': 'rgba(0, 0, 0, 0.5)'
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
    
    # Map states to progress percentages
    stage_progress = {
        7: 100, 6: 84, 5: 70, 4: 56, 3: 42, 2: 28, 1: 17
    }
    
    progress_height = stage_progress.get(state, 17)
    
    return {
        'width': '10px', 'height': f"{progress_height}%",
        'background-color': 'white', 'transition': 'height 0.5s ease-in-out'
    }

# Callback for updating connection status
@app.callback(
    dash.dependencies.Output('connection-status', 'children'),
    dash.dependencies.Output('connection-status', 'style'),
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_connection_status(n):
    global is_connected
    
    if is_connected:
        return "CONNECTED", {'color': '#00FF00', 'backgroundColor': 'rgba(0, 0, 0, 0.5)'}
    else:
        return "DISCONNECTED", {'color': '#FF0000', 'backgroundColor': 'rgba(0, 0, 0, 0.5)'}

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

# Start the serial reader thread
if __name__ == '__main__':
    # Start serial reader thread
    serial_thread = threading.Thread(target=serial_reader, daemon=True)
    serial_thread.start()
    
    # Run the Dash app
    app.run(debug=False)  # Removed blue debug icon on bottom right