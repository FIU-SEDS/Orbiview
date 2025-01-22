import cv2
import streamlit as st
import threading

# Streamlit configuration
st.title("Live Video Stream")

# Global variable to manage the camera feed
stop_feed = False

# Function to read and display video
def video_stream():
    global stop_feed
    # Open the default camera (camera index 0)
    cap = cv2.VideoCapture(0)
    
    # Stream video in real-time
    while not stop_feed:
        ret, frame = cap.read()
        if not ret:
            st.warning("Failed to grab frame. Exiting...")
            break
        
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Display the video frame
        st.image(frame, channels="RGB", caption="Live Camera Feed")
    
    # Release the camera after stopping
    cap.release()

# Start the video stream in a separate thread
video_thread = threading.Thread(target=video_stream)
video_thread.start()

# Streamlit button to stop video feed
if st.button("Stop Video Feed"):
    stop_feed = True
    video_thread.join()
    st.success("Video feed stopped.")
