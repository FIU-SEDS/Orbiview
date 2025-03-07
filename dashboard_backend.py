import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.transforms as transforms
import time
from math import atan2, sqrt, degrees

st.set_page_config(layout="wide")
st.logo("assets/FIU_LOGO.png")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Pages", ["Live Data Feed", "CSV Data Analysis"])

# Function to calculate orientation from accelerometer data
def calculate_orientation(accel_x, accel_y, accel_z):
    """
    Calculate pitch and roll angles from accelerometer data
    using arctangent method.
    
    Returns: (pitch, roll) in degrees
    """
    # Convert inputs to float to ensure math operations work
    accel_x = float(accel_x)
    accel_y = float(accel_y)
    accel_z = float(accel_z)
    
    # Calculate pitch (rotation around X-axis)
    pitch = degrees(atan2(accel_y, sqrt(accel_x**2 + accel_z**2)))
    
    # Calculate roll (rotation around Y-axis)
    roll = degrees(atan2(-accel_x, accel_z))
    
    return pitch, roll

# Function to plot rocket with 3D orientation
def plot_rocket_3d(pitch, roll):
    """
    Plot rocket with proper 3D orientation based on pitch and roll
    """
    fig, ax = plt.subplots(figsize=(4, 4), facecolor='none')
    img = mpimg.imread("assets/rocket.png")
    
    # Apply rotation transformations in the correct order
    # Note: Order of transformations matters! We apply roll first, then pitch
    trans = (transforms.Affine2D().rotate_deg(roll) +   # Roll around Y-axis
             transforms.Affine2D().rotate_deg(pitch) +  # Pitch around X-axis
             ax.transData)
    
    ax.imshow(img, extent=[-0.5, 0.5, -0.5, 0.5], transform=trans, alpha=1.0)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')
    
    # Add orientation information text
    ax.text(0.02, 0.02, f"Pitch: {pitch:.1f}°\nRoll: {roll:.1f}°", 
            transform=ax.transAxes, fontsize=10, 
            bbox=dict(facecolor='white', alpha=0.7))
    
    plt.close(fig)
    return fig

if page == "Live Data Feed":
    csv_file = "parsed_data.csv"  # Path to the CSV file

    with st.container():
        col1, col2, col3, col4 = st.columns(4, border=True)
        
        with col1:
            st.subheader("Acceleration")
            accel_placeholder = st.empty()

        with col2:
            st.subheader("Gyroscope")
            gyro_placeholder = st.empty()

        with col3:
            st.subheader("RSSI")
            signal_placeholder = st.empty()

        with col4:
            st.subheader("Signal To Noise")
            signal_to_noise_placeholder = st.empty()
    
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center;'>Telemetry</h3>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8, border=False)

        with col1:
            acceler_x_metric = st.metric("Acceleration X","-")
        
        with col2:
            acceler_y_metric = st.metric("Acceleration Y","-")

        with col3:
            acceler_z_metric = st.metric("Acceleration Z","-")
        
        with col4:
            gyro_x_metric = st.metric("Gyro X","-")

        with col5:
            gyro_y_metric = st.metric("Gyro Y","-")

        with col6:
            gyro_z_metric = st.metric("Gyro Z","-")

        with col7:
            time_metric = st.metric("Time","-")

        with col8:
            state_metric = st.metric("State","-")


    with st.container():
        st.subheader("Rocket Orientation")
        plot_placeholder = st.empty()
    
    # Initialize variables for sensor fusion
    pitch_filtered = 0
    roll_filtered = 0
    last_time = None
    
    while True:
        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                st.warning("CSV file is empty. Waiting for data...")
                time.sleep(1)
                continue

            # Rename time_elapsed column to Time for compatibility with existing code
            df = df.rename(columns={"time_elapsed": "Time"})
            
            latest_data = df.iloc[-1]  
            
            # Create DataFrames for acceleration and gyroscope data
            accel_data = df[["Time", "acceleration_x", "acceleration_y", "acceleration_z"]].set_index("Time")
            gyro_data = df[["Time", "gyro_x", "gyro_y", "gyro_z"]].set_index("Time")
            signal_to_noise_data = df[["Time", "signal_to_noise"]].set_index("Time")
            
            # Plot the three acceleration and gyro components
            accel_placeholder.line_chart(accel_data)
            gyro_placeholder.line_chart(gyro_data)
            signal_to_noise_placeholder.line_chart(signal_to_noise_data)
            signal_placeholder.line_chart(df.set_index("Time")["rssi"])
            
            # Get the latest accelerometer data
            latest_accel_x = latest_data.get("acceleration_x", 0)
            latest_accel_y = latest_data.get("acceleration_y", 0)
            latest_accel_z = latest_data.get("acceleration_z", 0)
            
            # Get the latest gyroscope data
            latest_gyro_x = latest_data.get("gyro_x", 0)
            latest_gyro_y = latest_data.get("gyro_y", 0)
            latest_gyro_z = latest_data.get("gyro_z", 0)
            
            # Get latest time
            latest_time = latest_data.get("Time", 0)
            
            # Calculate orientation directly from accelerometer
            pitch, roll = calculate_orientation(latest_accel_x, latest_accel_y, latest_accel_z)
            
            # Apply basic complementary filter for more stable readings
            # This helps reduce noise and jitter in the visualization
            alpha = 0.8  # Weight for the filter (higher = more gyro influence)
            
            if last_time is not None:
                # Calculate time delta in seconds (assuming time is in milliseconds)
                dt = (latest_time - last_time) / 1000.0
                
                # Apply complementary filter
                # Gyro data is typically in degrees per second, may need scaling
                gyro_scale = 0.01  # Adjust this based on your sensor's sensitivity
                
                # Update filtered values
                pitch_filtered = alpha * (pitch_filtered + latest_gyro_x * gyro_scale * dt) + (1 - alpha) * pitch
                roll_filtered = alpha * (roll_filtered + latest_gyro_y * gyro_scale * dt) + (1 - alpha) * roll
            else:
                # First reading
                pitch_filtered = pitch
                roll_filtered = roll
            
            # Store current time for next iteration
            last_time = latest_time
            
            # Plot the rocket with calculated orientation
            fig = plot_rocket_3d(pitch_filtered, roll_filtered)
            plot_placeholder.pyplot(fig)
             
            # Update metrics
            acceler_x_metric.metric("Acceleration X", latest_accel_x if latest_accel_x is not None else "N/A")
            acceler_y_metric.metric("Acceleration Y", latest_accel_y if latest_accel_y is not None else "N/A")
            acceler_z_metric.metric("Acceleration Z", latest_accel_z if latest_accel_z is not None else "N/A")
            
            gyro_x_metric.metric("Gyro X", latest_gyro_x if latest_gyro_x is not None else "N/A")
            gyro_y_metric.metric("Gyro Y", latest_gyro_y if latest_gyro_y is not None else "N/A")
            gyro_z_metric.metric("Gyro Z", latest_gyro_z if latest_gyro_z is not None else "N/A")

            time_metric.metric("Time", latest_time if latest_time is not None else "N/A")
        
            latest_state = latest_data.get("rocket_state", -1)
            state_names = {
                0: "INIT",
                1: "IDLE",
                2: "BOOST",
                3: "APOGEE",
                4: "DROGUE_DEPLOY",
                5: "MAIN_DEPLOY",
                6: "LANDED"
            }

            state_name = state_names.get(latest_state, "UNKNOWN")
            state_metric.metric("State", state_name)

            time.sleep(1)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            time.sleep(1)

elif page == "CSV Data Analysis":
    st.title("CSV Data Analysis")
    data = st.file_uploader("Choose CSV File to Read", type='csv')
    if data is not None:
        df = pd.read_csv(data)
        # Rename time_elapsed for consistency if needed
        if "time_elapsed" in df.columns and "Time" not in df.columns:
            df = df.rename(columns={"time_elapsed": "Time"})
            
        tab1, tab2, tab3 = st.tabs(["Acceleration (X,Y,Z)", "Gyroscope (X,Y,Z)", "Signal Strength"])
        
        with tab1:
            st.header("Acceleration Components Chart")
            accel_data = df[["Time", "acceleration_x", "acceleration_y", "acceleration_z"]].set_index("Time")
            st.line_chart(accel_data)
        
        with tab2:
            st.header("Gyroscope Components Chart")
            gyro_data = df[["Time", "gyro_x", "gyro_y", "gyro_z"]].set_index("Time")
            st.line_chart(gyro_data)
        
        with tab3:
            st.header("Signal Strength Chart")
            st.line_chart(df.set_index("Time")["rssi"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            max_accel = max(
                df["acceleration_x"].max(),
                df["acceleration_y"].max(),
                df["acceleration_z"].max()
            )
            st.metric("Max Acceleration Component", max_accel)
        with col2:
            max_gyro = max(
                df["gyro_x"].abs().max(),
                df["gyro_y"].abs().max(),
                df["gyro_z"].abs().max()
            )
            st.metric("Max Gyro Component", max_gyro)
        with col3:
            st.metric("Min Signal Strength", df["rssi"].min())