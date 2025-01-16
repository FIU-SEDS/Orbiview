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
    col1, col2, col3 = st.columns(3, border=True)
    
    with col1:
        st.subheader("Rocket State")
        data = pd.DataFrame(
            np.random.randn(50,3),
            columns=["State1", "State2", "State3"])
        
        st.line_chart(data)
        
    with col2:
        st.subheader("Live Feed")
        