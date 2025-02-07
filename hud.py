import streamlit as st

st.set_page_config(layout="wide")

# Custom HTML & JavaScript for full-screen live camera feed
camera_html = """
    <style>
        body, html {
            margin: 0;
            padding: 0;
            overflow: hidden;
            width: 100%;
            height: 100%;
        }
        .video-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            z-index: -1;
        }
        video {
            width: 100vw;
            height: 100vh;
            object-fit: cover;
        }
    </style>
    <div class="video-container">
        <video id="video" autoplay playsinline></video>
    </div>
    <script>
        async function startCamera() {
            const video = document.getElementById('video');
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
                video.srcObject = stream;
            } catch (error) {
                console.error("Camera access denied or not available:", error);
            }
        }
        startCamera();
    </script>
"""

# Render the HTML inside an iframe, making sure it's full-screen
st.components.v1.html(camera_html, height=700, width=1000)  # Adjust dimensions if needed

# UI overlay elements (they stay on top)
st.markdown("<h1 style='color: white; text-align: center;'>HUD Interface</h1>", unsafe_allow_html=True)
st.sidebar.header("Settings")
st.sidebar.checkbox("Enable Overlay")
