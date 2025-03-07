import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.transforms as transforms
import time

st.set_page_config(layout="wide")
st.logo("assets/FIU_logo.png")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Pages", ["Live Data Feed", "CSV Data Analysis"])

if page == "Live Data Feed":
    csv_file = "parsed_data.csv"  # Path to the CSV file

    with st.container():
        col1, col2, col3 = st.columns(3, border=True)
        
        with col1:
            st.subheader("IMU Acceleration")
            accel_placeholder = st.empty()

        with col2:
            st.subheader("Altitude")
            altitude_placeholder = st.empty()

        with col3:
            st.subheader("Signal Strength (RSSI)")
            signal_placeholder = st.empty()
    
    with st.container():
        col1, col2 = st.columns(2, border=True)

        with col1:
            plot_placeholder = st.empty()

        with col2:
            st.subheader("Raw Telemetry")
            with st.container():
                col1, col2, col3 = st.columns(3,border=False)

                with col1:
                    altitude_metric = st.metric("Altitude (m)", "-")
                    speed_metric = st.metric("Speed (m/s)", "-")

                with col2:
                    acceleration_metric = st.metric("Acceleration (m/s²)", "-")
                    pressure_metric = st.metric("Pressure (hPa)", "-")

                with col3:
                    signal_strength_metric = st.metric("Signal Strength (%)", "-")


            
    
    def plot_rocket(angle):
        fig, ax = plt.subplots(figsize=(2, 2), facecolor='none')
        img = mpimg.imread("assets/rocket.png")
        trans = transforms.Affine2D().rotate_deg(angle) + ax.transData
        ax.imshow(img, extent=[-0.5, 0.5, -0.5, 0.5], transform=trans, alpha=1.0)
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect('equal')
        plt.close(fig) 
        return fig
    
    while True:
        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                st.warning("CSV file is empty. Waiting for data...")
                time.sleep(1)
                continue

            latest_data = df.iloc[-1]  
            
            altitude_placeholder.line_chart(df.set_index("Time")["Altitude"])
            accel_placeholder.line_chart(df.set_index("Time")["Acceleration"])
            signal_placeholder.line_chart(df.set_index("Time")["RSSI"])
            
            altitude_value = latest_data.get("Altitude", None)
            speed_value = latest_data.get("Speed", None)
            acceleration_value = latest_data.get("Acceleration", None)
            pressure_value = latest_data.get("Pressure", None)
            signal_strength_value = latest_data.get("RSSI", None)

            #BASICALLY IF BLANK IT LEAVES BLANK
            altitude_metric.metric("Altitude (m)", f"{altitude_value:.2f}" if altitude_value is not None else "N/A")
            speed_metric.metric("Speed (m/s)", f"{speed_value:.2f}" if speed_value is not None else "N/A")
            acceleration_metric.metric("Acceleration (m/s²)", f"{acceleration_value:.2f}" if acceleration_value is not None else "N/A")
            pressure_metric.metric("Pressure (hPa)", f"{pressure_value:.2f}" if pressure_value is not None else "N/A")
            signal_strength_metric.metric("Signal Strength (%)", signal_strength_value if signal_strength_value is not None else "N/A")

            
            rocket_angle = latest_data.get("angle", 0)  #ROCKET ANGLE, INPUT CALCULATE idk how to calculate
            fig = plot_rocket(rocket_angle)
            plot_placeholder.pyplot(fig)
        
            time.sleep(1)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            time.sleep(1)

elif page == "CSV Data Analysis":
    st.title("CSV Data Analysis")
    data = st.file_uploader("Choose CSV File to Read", type='csv')
    if data is not None:
        df = pd.read_csv(data)
        tab1, tab2, tab3 = st.tabs(["Altitude", "Acceleration", "Signal Strength"])
        
        with tab1:
            st.header("Altitude Chart")
            st.line_chart(df.set_index("Time")["Altitude"])
        
        with tab2:
            st.header("Acceleration Chart")
            st.line_chart(df.set_index("Time")["Acceleration"])
        
        with tab3:
            st.header("Signal Strength Chart")
            st.line_chart(df.set_index("Time")["RSSI"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Max Altitude", df["altitude"].max())
        with col2:
            st.metric("Max Acceleration", df["acceleration"].max())
        with col3:
            st.metric("Min Signal Strength", df["rssi"].min())
