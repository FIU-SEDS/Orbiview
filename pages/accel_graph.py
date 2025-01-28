import streamlit as st
import time
import numpy as np
import pandas as pd

st.set_page_config(page_title="Altitude Post-Flight Demo", page_icon="📈")

with st.container():
    st.markdown("# Altitude Post-Flight Data")  
    st.write(
        """This demo was used with pandas and streamlit line chart plotting designed for post-flight data that specifically measures altitude respective to the time."""
    )

with st.container():
    altitude_graph, altitude_data = st.columns([4,1], vertical_alignment='bottom')
    
    with altitude_graph:
        flight_altitude_data = pd.read_csv('assets/time_height.csv', usecols=['time','height'])
        flight_altitude_data.set_index('time', inplace=True)

        chart = st.line_chart(flight_altitude_data)
        
    with altitude_data: 
        st.dataframe(flight_altitude_data)


# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")