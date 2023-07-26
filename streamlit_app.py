import os
import av
import threading
import streamlit as st
import streamlit_nested_layout
from streamlit_webrtc import VideoHTMLAttributes, webrtc_streamer

from audio_handling import AudioFrameHandler
from drowsy_detection import VideoFrameHandler



# Define the audio file to use.
alarm_file_path = os.path.join("audio", "wake_up_vi.wav")

# Streamlit Components
st.set_page_config(
    page_title="Drowsiness Detection",
    page_icon="https://media.licdn.com/dms/image/C4E03AQH6bPZc60xNlw/profile-displayphoto-shrink_800_800/0/1585720891986?e=2147483647&v=beta&t=r-lVoNNR3CB5yQEqNfLrvYumGRtEtjGFig_b6Il2oSUhttps://media.licdn.com/dms/image/C4E03AQH6bPZc60xNlw/profile-displayphoto-shrink_800_800/0/1585720891986?e=2147483647&v=beta&t=r-lVoNNR3CB5yQEqNfLrvYumGRtEtjGFig_b6Il2oSU",
    layout="wide",  # centered, wide
    initial_sidebar_state="expanded",
    
)


col1, col2 = st.columns(spec=[6, 2], gap="medium")

with col1:
    st.title("Bài tập lớn - Hệ thống phát hiện buồn ngủ")
    with st.container():
        c1, c2 = st.columns(spec=[1, 1])
        with c1:
            # The amount of time (in seconds) to wait before sounding the alarm.
            WAIT_TIME = st.slider("Thời gian đợi trước khi kích hoạt thông báo (giây):", 0.0, 5.0, 1.0, 0.25)

        with c2:
            # Lowest valid value of Eye Aspect Ratio. Ideal values [0.15, 0.2].
            EAR_THRESH = st.slider("Ngưỡng cho EAR - Eye Aspect Ratio:", 0.0, 0.4, 0.18, 0.01)

thresholds = {
    "EAR_THRESH": EAR_THRESH,
    "WAIT_TIME": WAIT_TIME,
}

# For streamlit-webrtc
video_handler = VideoFrameHandler()
audio_handler = AudioFrameHandler(sound_file_path=alarm_file_path)

lock = threading.Lock()  # For thread-safe access & to prevent race-condition.
shared_state = {"play_alarm": False}


def video_frame_callback(frame: av.VideoFrame):
    frame = frame.to_ndarray(format="bgr24")  # Decode and convert frame to RGB

    frame, play_alarm = video_handler.process(frame, thresholds)  # Process frame
    with lock:
        shared_state["play_alarm"] = play_alarm  # Update shared state

    return av.VideoFrame.from_ndarray(frame, format="bgr24")  # Encode and return BGR frame


def audio_frame_callback(frame: av.AudioFrame):
    with lock:  # access the current “play_alarm” state
        play_alarm = shared_state["play_alarm"]

    new_frame: av.AudioFrame = audio_handler.process(frame, play_sound=play_alarm)
    return new_frame


# https://github.com/whitphx/streamlit-webrtc/blob/main/streamlit_webrtc/config.py

with col1:
    ctx = webrtc_streamer(
        key="drowsiness-detection",
        video_frame_callback=video_frame_callback,
        audio_frame_callback=audio_frame_callback,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},  # Add this to config for cloud deployment.
        media_stream_constraints={"video": {"height": {"ideal": 480}}, "audio": True},
        video_html_attrs=VideoHTMLAttributes(autoPlay=True, controls=False, muted=False),
    )


