import streamlit as st
import numpy as np
import pandas as pd

import time
import random

st.set_page_config(layout="wide")

st.logo("assets/FIU_LOGO.png")


with st.container():
    col1, col2, col3, col4 = st.columns(4,border=True)
    
    with col1:
        st.subheader("LowG IMU Acceleration")
        data = np.random.randn(50)
        st.line_chart(data)

    with col2:
        st.subheader("LowG IMU Gyroscope")
        data = pd.DataFrame(np.random.randn(50, 3), columns=["x", "y", "z"])
        st.line_chart(data)
        

    with col3:
        st.subheader("Signal Strength (RSSI)")
        sf_time_data = []
        signal_strength_data = []
        graph_placeholder = st.empty()

    with col4:
        st.subheader("GPS Altitude")
        time_data = []
        altitude_data = []
        chart_placeholder = st.empty()



with st.container():
    col1, col2, col3 = st.columns(3,border=True)

    with col1:
        st.subheader("State Estimation")
        data = pd.DataFrame(np.random.randn(50, 3), columns=["State1", "State2", "State3"])
        st.line_chart(data)

    with col2:
        st.subheader("Live Feed")
        camera_html = """
        <div style="text-align: center;">
            <video id="video" autoplay style="width: 100%; max-width: 600px; border: 1px solid black;"></video>
        </div>
        <script>
            async function startCamera() {
                const video = document.getElementById('video');
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                        video.srcObject = stream;
                    } catch (error) {
                        console.error("Camera access denied or not available:", error);
                    }
                } else {
                    console.error("getUserMedia not supported by this browser.");
                }
            }
            startCamera();
        </script>
        """
        st.components.v1.html(camera_html, height=400)

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

    time.sleep(1)
