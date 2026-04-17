import streamlit as st
import cv2
import requests
import asyncio
import websockets
import json
import time

API_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/authenticate"

st.set_page_config(page_title="Real-Time Face ID", layout="wide")
st.title("🛡️ Real-Time Face ID Entry")

tab1, tab2 = st.tabs(["🔐 Live Entry Camera", "📝 Enroll User"])

# --- TAB 1: REAL-TIME AUTHENTICATION ---
with tab1:
    st.write("Camera is running. Step in front of the lens.")
    run_auth = st.checkbox("Start Live Scanner")
    FRAME_WINDOW = st.image([])

    async def run_live_scanner():
        cap = cv2.VideoCapture(0) # Open default webcam
        
        # State variables for the debounce/cooldown logic
        cooldown_until = 0
        banner_text = ""
        banner_color = (0, 0, 0)
        
        async with websockets.connect(WS_URL) as websocket:
            while run_auth:
                ret, frame = cap.read()
                if not ret:
                    st.error("Failed to capture video.")
                    break
                
                current_time = time.time()
                
                # Check if we are currently in a cooldown period
                if current_time < cooldown_until:
                    # Draw dynamic Banner (Green for Granted, Red for Denied)
                    cv2.rectangle(frame, (0, frame.shape[0] - 80), (frame.shape[1], frame.shape[0]), banner_color, -1)
                    cv2.putText(frame, banner_text, (30, frame.shape[0] - 25), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
                else:
                    # Not in cooldown. Compress and send frame to AI backend for scanning.
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    await websocket.send(buffer.tobytes())
                    
                    # Receive bounding boxes and names
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    # Draw boxes on the frame
                    for face in data.get("faces", []):
                        box = face["box"]
                        name = face["name"]
                        
                        # Color logic for the bounding box
                        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                        
                        cv2.rectangle(frame, (box["left"], box["top"]), (box["right"], box["bottom"]), color, 2)
                        cv2.putText(frame, name, (box["left"], box["top"] - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                        
                        # --- ASYMMETRIC COOLDOWN LOGIC ---
                        if name != "Unknown":
                            # Known user: 3-second pause to walk through the door
                            cooldown_until = current_time + 3.0 
                            banner_text = f"ACCESS GRANTED: {name.upper()}"
                            banner_color = (0, 255, 0) 
                        else:
                            # Unknown user: 1-second pause to flash warning, then try again quickly
                            cooldown_until = current_time + 1.0 
                            banner_text = "ACCESS DENIED: UNKNOWN"
                            banner_color = (0, 0, 255) 
                            
                        # Break out of the loop so it only triggers the door logic for the primary detected face
                        break 

                # Convert BGR to RGB for Streamlit rendering
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                FRAME_WINDOW.image(frame)
                
        cap.release()

    if run_auth:
        asyncio.run(run_live_scanner())

# --- TAB 2: REAL-TIME ENROLLMENT ---
with tab2:
    st.header("Admin: Enroll New User")
    enroll_name = st.text_input("Enter User Name:")
    
    st.write("Ensure your face is clearly visible, then click capture.")
    run_enroll = st.checkbox("Turn on Camera for Enrollment")
    ENROLL_WINDOW = st.image([])
    
    if run_enroll:
        cap2 = cv2.VideoCapture(0)
        ret, frame2 = cap2.read()
        
        if ret:
            # Show live feed for framing
            frame2_rgb = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
            ENROLL_WINDOW.image(frame2_rgb)
            
            if st.button("Capture & Enroll") and enroll_name:
                with st.spinner("Extracting template..."):
                    _, buffer = cv2.imencode('.jpg', frame2)
                    files = {"file": ("image.jpg", buffer.tobytes(), "image/jpeg")}
                    try:
                        res = requests.post(f"{API_URL}/enroll", params={"name": enroll_name}, files=files)
                        if res.status_code == 200:
                            st.success(res.json()["message"])
                        else:
                            st.error(res.json()["detail"])
                    except Exception as e:
                        st.error(f"Backend error: {e}")
        cap2.release()