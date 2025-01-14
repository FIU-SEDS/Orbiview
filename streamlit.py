import streamlit as st
import random
import time

# Initialize Streamlit App
st.set_page_config(
    page_title="Rocket Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Global variables to store simulated data
rocket_states = ["Idle", "Ascending", "Coasting", "Descending", "Landed"]

# Function to simulate rocket data
def generate_rocket_data(start_time):
    current_time = time.time() - start_time
    altitude = random.uniform(0, 100)  # Random altitude between 0 and 100
    speed = random.uniform(0, 50)  # Random speed between 0 and 50
    state = random.choice(rocket_states)
    elapsed_time = f"T+ {int(current_time // 60):02}:{int(current_time % 60):02}:{int((current_time % 1) * 100):02}"
    return altitude, speed, state, elapsed_time

# Simulated start time
start_time = time.time()

# Background video using Streamlit's HTML capabilities
st.markdown(
    """
    <style>
    .stApp {
        background: url('https://www.example.com/background.mp4') no-repeat center center fixed;
        background-size: cover;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Layout for telemetry data
st.markdown("<h1 style='text-align: center; color: white;'>🚀 FIU SEDS Rocket Dashboard 🚀</h1>", unsafe_allow_html=True)

# Container for telemetry and stage info
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<h2 style='color: white;'>Telemetry</h2>", unsafe_allow_html=True)
    altitude = st.empty()
    speed = st.empty()

with col2:
    st.markdown("<h2 style='color: white;'>Current Stage</h2>", unsafe_allow_html=True)
    stage = st.empty()

with col3:
    st.markdown("<h2 style='color: white;'>Mission Time</h2>", unsafe_allow_html=True)
    mission_time = st.empty()

# Rocket stage progress bar and footer
st.markdown(
    "<div style='position: fixed; bottom: 0; width: 100%; background: rgba(0, 0, 0, 0.7); color: white; text-align: center; padding: 10px;'>"
    "<h3>LAUNCH: FIU SEDS Sub-Scale</h3>"
    "</div>",
    unsafe_allow_html=True,
)

# Continuously update data
while True:
    altitude_value, speed_value, state, elapsed = generate_rocket_data(start_time)
    altitude.metric("Altitude", f"{altitude_value:.2f} km")
    speed.metric("Speed", f"{speed_value:.2f} km/h")
    stage.write(f"<h3 style='color: white;'>{state}</h3>", unsafe_allow_html=True)
    mission_time.write(f"<h3 style='color: white;'>{elapsed}</h3>", unsafe_allow_html=True)
    time.sleep(1)
