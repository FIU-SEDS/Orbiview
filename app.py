import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.transforms as transforms

import time
import random

st.set_page_config(layout="wide")

st.logo("assets/FIU_LOGO.png")


# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Pages", ["Live Data Feed", "CSV Data Analysis"])

# Page content
if page == "Live Data Feed":

    with st.container():
        col1, col2, col3 = st.columns(3,border=True)
        
        with col1:
            st.subheader("LowG IMU Acceleration")
            data = np.random.randn(50)
            st.line_chart(data)

        with col2:
            st.subheader("GPS Altitude")
            time_data = []
            altitude_data = []
            chart_placeholder = st.empty()
            

        with col3:
            plot_placeholder = st.empty()



    with st.container():
        col1, col2, col3 = st.columns(3,border=True)

        with col1:
            st.subheader("Signal Strength (RSSI)")
            sf_time_data = []
            signal_strength_data = []
            graph_placeholder = st.empty()

        with col2:
            st.subheader("Speed")
            data = np.random.randn(50)
            st.line_chart(data)

        with col3:
            st.subheader("Raw Telemetry")
            with st.container():
                col1, col2, col3 = st.columns(3)
                with col1:
                    altitude_placeholder = st.empty()
                    velocity_placeholder = st.empty()
                with col2:
                    temperature_placeholder = st.empty()
                    pressure_placeholder = st.empty()
                with col3:
                    signal_strength_placeholder = st.empty()
                    state_placeholder = st.empty()

        
    with st.container():

        # Rocket Stages
        stages = ["Init", "Idle", "Boost", "Coast", "Apogee", "Drogue", "Main Chute", "Landed"]
        stage_placeholder = st.empty()  # Placeholder for stage text
        progress_bar = st.progress(0)   # Progress bar at the bottom

    
    def plot_rocket(angle):
        fig, ax = plt.subplots(figsize=(2, 2), facecolor='none')  # Transparent background
    
        # Load rocket image (make sure 'rocket.png' is in the same directory or specify the full path)
        img = mpimg.imread("assets/rocket.png")  # Use a transparent PNG

        # Rotate image
        trans = transforms.Affine2D().rotate_deg(angle) + ax.transData

        # Display the image
        ax.imshow(img, extent=[-0.5, 0.5, -0.5, 0.5], transform=trans, alpha=1.0)

        # Hide axes
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"Rocket Orientation: {angle}°", color='white')  # White text
        ax.set_aspect('equal')

        # Transparent background
        ax.set_facecolor('none')
        fig.patch.set_alpha(0)

        return fig

    # Initialize angle before the loop
    angle = 0  



    for i in range(100):  # Simulate 100 updates

        # Update rocket stage based on progress
        stage_index = min(i // (100 // len(stages)), len(stages) - 1)  # Calculate stage index
        stage_placeholder.subheader(f"Rocket Stage: {stages[stage_index]}")  # Display current stage
        progress_bar.progress(i + 1)  # Update progress bar (0-100%)


        # Simulate new data points
        new_time = i
        new_altitude = np.sin(i * 0.1) * 100  # Simulate altitude (meters)

        # Append new data
        time_data.append(new_time)
        altitude_data.append(new_altitude)

        # Create a DataFrame for the chart
        df = pd.DataFrame({
            "Time (s)": time_data,
            "Altitude (m)": altitude_data
        })
        # Update the chart in the placeholder
        chart_placeholder.line_chart(df.set_index("Time (s)"))


        sf_new_time = i
        new_signal_strength = np.random.randint(50, 100)  # Simulate signal strength (%)

        # Append new data
        sf_time_data.append(sf_new_time)
        signal_strength_data.append(new_signal_strength)

        # Create a DataFrame for plotting
        sf = pd.DataFrame({
            "Time (s)": sf_time_data,
            "Signal Strength (%)": signal_strength_data
        })

        # Plot the data
        graph_placeholder.line_chart(sf.set_index("Time (s)"))

        altitude = int(new_altitude)
        velocity = int(new_signal_strength) 
        temperature = random.uniform(-20, 40)  
        pressure = random.uniform(900, 1100)  
        signal_strength = random.randint(0, 100)  
        state = stages[stage_index]

        # Update placeholders with new data
        altitude_placeholder.metric("Altitude (m)", f"{altitude}")
        velocity_placeholder.metric("Velocity (m/s)", f"{velocity}")
        temperature_placeholder.metric("Temperature (°C)", f"{temperature:.1f}")
        pressure_placeholder.metric("Pressure (hPa)", f"{pressure:.1f}")
        signal_strength_placeholder.metric("Signal Strength (%)", f"{signal_strength}")
        state_placeholder.metric("State", state)

        
        fig = plot_rocket(angle)
        plot_placeholder.pyplot(fig)  # Update the plot
        angle_change = random.choice([-5, 5])
        angle = (angle + angle_change) % 36
        plot_placeholder.pyplot(fig, clear_figure=True) 
    

        time.sleep(0.1)


elif page == "CSV Data Analysis":
    st.title("CSV Data Analysis")

    data = st.file_uploader("Choose CSV File to Read",type='csv')
    if data is not None:
        tab1, tab2, tab3 = st.tabs(["Height","Speed","Temperature"])
        with tab1:
            df = pd.read_csv(data, usecols=['time','height'])
            df.set_index('time', inplace=True)
            st.header("Height Chart")
            chart = st.line_chart(df)
        with tab2:
            data.seek(0)
            df = pd.read_csv(data, usecols=['time','speed'])
            df.set_index('time', inplace=True)
            st.header("Speed Chart:")
            chart = st.line_chart(df)
        with tab3:
            data.seek(0)
            df = pd.read_csv(data, usecols=['time','temperature'])
            df.set_index('time', inplace=True)
            st.header("Temperature Chart:")
            chart = st.line_chart(df)

        
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            data.seek(0)
            h = pd.read_csv(data, usecols=['height'])  
            max_height = h['height'].max() 
            st.metric(label="Max Height", value=max_height)
            
        with col2:
            data.seek(0) 
            s = pd.read_csv(data, usecols=['speed'])  
            max_speed = s['speed'].max()
            st.metric(label="Max Speed", value=max_speed)

        with col3:
            data.seek(0) 
            s = pd.read_csv(data, usecols=['temperature'])  
            avg_temp = s['temperature'].mean()
            st.metric(label="Average Temperature", value=avg_temp)
        
        with col4:
            data.seek(0) 
            s = pd.read_csv(data, usecols=['time'])  
            total_time = s['time'].max()
            st.metric(label="Total time", value=total_time)

