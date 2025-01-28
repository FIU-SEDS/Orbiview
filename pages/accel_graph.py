import streamlit as st
import time
import numpy as np
import pandas as pd

st.set_page_config(page_title="Plotting Demo", page_icon="📈")

st.markdown("# Plotting Demo")
st.sidebar.header("Plotting Demo")
st.write(
    """This demo illustrates a combination of plotting and animation with
Streamlit. We're generating a bunch of random numbers in a loop for around
5 seconds. Enjoy!"""
)

height_data = pd.read_csv('../assests/time_height.csv', usecols=['height'])
time_data = pd.read_csv('../assets/time_height.csv', usecols=['time'])
chart = st.line_chart(height_data, x=time_data, y_label="Height")


# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")