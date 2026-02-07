# Real-time playing card detection using YOLOv8 + Streamlit
#
# Install dependencies:
#   pip install -r requirements.txt
#
# Run:
#   streamlit run app.py

import base64
import io
import time

import cv2
import streamlit as st
from PIL import Image

try:
    from streamlit_extras.badges import badge
except ImportError:
    badge = None

from config import SUIT_BGR
from detection import compute_card_states, load_model
from renderer import (
    render_info_panel,
    render_progress_bar,
    render_suit_icons,
    render_suit_images,
)
from styles import PAGE_CSS, SUIT_DIVIDER


def frame_to_base64(frame_rgb):
    """Convert RGB frame to base64 encoded JPEG string."""
    pil_image = Image.fromarray(frame_rgb)
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=85)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

st.set_page_config(layout="wide", page_title="Card Detection")
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# Modern header (shadcn/TailwindUI-inspired)
header_html = """
<div style="text-align:center;margin-bottom:24px;padding:24px 0;">
    <h1 style="font-size:2rem;font-weight:700;color:hsl(210 40% 98%);margin:0 0 8px 0;letter-spacing:-0.025em;">
        Playing Card Detection
    </h1>
    <p style="font-size:0.875rem;color:hsl(217.9 10.6% 64.9%);margin:0;">
        Real-time card recognition powered by <strong style="color:hsl(221.2 83.2% 53.3%);">YOLOv8</strong>
    </p>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# --- Card style ---
if "card_style" not in st.session_state:
    st.session_state.card_style = "Icons"
if "switching_mode" not in st.session_state:
    st.session_state.switching_mode = False

# --- Layout: left cards | camera | right cards ---
left_col, center_col, right_col = st.columns([1, 2, 1])

with left_col:
    left_placeholder = st.empty()
with right_col:
    right_placeholder = st.empty()
with center_col:
    progress_placeholder = st.empty()
    frame_placeholder = st.empty()

    if "running" not in st.session_state:
        st.session_state.running = False

    def toggle():
        st.session_state.running = not st.session_state.running

    def set_icons():
        if st.session_state.card_style != "Icons":
            st.session_state.switching_mode = True
            st.session_state.card_style = "Icons"
            # Use cached HTML if available for instant switch
            if st.session_state.cached_icons_html["left"]:
                left_placeholder.markdown(st.session_state.cached_icons_html["left"], unsafe_allow_html=True)
                right_placeholder.markdown(st.session_state.cached_icons_html["right"], unsafe_allow_html=True)
            elif st.session_state.last_card_states:
                update_side_panels(st.session_state.last_card_states)

    def set_images():
        if st.session_state.card_style != "Images":
            st.session_state.switching_mode = True
            st.session_state.card_style = "Images"
            # Use cached HTML if available for instant switch
            if st.session_state.cached_images_html["left"]:
                left_placeholder.markdown(st.session_state.cached_images_html["left"], unsafe_allow_html=True)
                right_placeholder.markdown(st.session_state.cached_images_html["right"], unsafe_allow_html=True)
            elif st.session_state.last_card_states:
                update_side_panels(st.session_state.last_card_states)

    # Add spacing to prevent overlay
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    # Modern toggle button group (shadcn-style visual, Streamlit buttons)
    icon_col, image_col = st.columns(2)
    with icon_col:
        st.button(
            "Icons",
            on_click=set_icons,
            use_container_width=True,
            type="primary" if st.session_state.card_style == "Icons" else "secondary",
            key="icons_btn"
        )
    with image_col:
        st.button(
            "Images",
            on_click=set_images,
            use_container_width=True,
            type="primary" if st.session_state.card_style == "Images" else "secondary",
            key="images_btn"
        )

    # Modern primary action button with spacing
    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    st.button(
        "⏹ Stop Detection" if st.session_state.running else "▶ Start Detection",
        on_click=toggle,
        use_container_width=True,
        type="primary",
        key="start_stop_btn"
    )
    
    # Status badge (if available)
    if badge:
        status_text = "Running" if st.session_state.running else "Idle"
        badge(icon_name="⚡" if st.session_state.running else "⏸", badge_text=status_text)

# --- Session state ---
if "card_history" not in st.session_state:
    st.session_state.card_history = {}
if "ever_detected" not in st.session_state:
    st.session_state.ever_detected = set()
if "last_frame_html" not in st.session_state:
    st.session_state.last_frame_html = None
if "last_card_states" not in st.session_state:
    st.session_state.last_card_states = {}
if "cached_icons_html" not in st.session_state:
    st.session_state.cached_icons_html = {"left": "", "right": ""}
if "cached_images_html" not in st.session_state:
    st.session_state.cached_images_html = {"left": "", "right": ""}


def update_side_panels(card_states):
    """Update side panels without refreshing the entire UI."""
    render = render_suit_images if st.session_state.card_style == "Images" else render_suit_icons
    left_info = render_info_panel("left")
    right_info = render_info_panel("right")
    left_html = left_info + render("C", card_states) + SUIT_DIVIDER + render("S", card_states)
    right_html = right_info + render("H", card_states) + SUIT_DIVIDER + render("D", card_states)
    
    # Cache the HTML for both modes to enable instant switching
    if st.session_state.card_style == "Icons":
        st.session_state.cached_icons_html = {"left": left_html, "right": right_html}
    else:
        st.session_state.cached_images_html = {"left": left_html, "right": right_html}
    
    # Update side panels - this should not cause frame refresh
    left_placeholder.markdown(left_html, unsafe_allow_html=True)
    right_placeholder.markdown(right_html, unsafe_allow_html=True)
    
    # Clear switching flag after update
    if st.session_state.get("switching_mode", False):
        st.session_state.switching_mode = False


# Show cards and progress bar in default state (only if not already initialized)
# Skip initial update if we're switching modes to prevent refresh
if not st.session_state.get("switching_mode", False):
    if not st.session_state.last_card_states:
        update_side_panels({})
        progress_placeholder.markdown(render_progress_bar(is_running=False), unsafe_allow_html=True)
    else:
        # Use last known states to avoid refresh
        update_side_panels(st.session_state.last_card_states)
        if not st.session_state.running:
            progress_placeholder.markdown(render_progress_bar(st.session_state.last_card_states, is_running=False), unsafe_allow_html=True)

# --- Initialize camera (always open) ---
if "camera_initialized" not in st.session_state:
    st.session_state.camera_initialized = False
    st.session_state.cap = None

# Initialize camera if not already done
if st.session_state.cap is None:
    st.session_state.cap = cv2.VideoCapture(0)
    st.session_state.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    st.session_state.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    st.session_state.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    st.session_state.camera_initialized = True

# --- Main camera and detection loop ---
if st.session_state.cap is not None and st.session_state.cap.isOpened():
    if st.session_state.running:
        # Detection mode - continuous loop
        model = load_model()
        
        while st.session_state.running:
            ret, frame = st.session_state.cap.read()
            if not ret:
                st.warning("Lost webcam feed.")
                break

            results = model(frame, imgsz=320, conf=0.85, verbose=False)
            now = time.time()

            current_detections = {}
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls_id = int(box.cls[0])
                name = model.names[cls_id]
                conf = float(box.conf[0])
                label = f"{name} ({int(conf * 100)}%)"

                if name not in current_detections or conf > current_detections[name]:
                    current_detections[name] = conf

                box_color = SUIT_BGR.get(name[-1], (0, 255, 0))
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_str = frame_to_base64(frame_rgb)
            frame_html = f'''
            <div class="camera-container">
                <img src="data:image/jpeg;base64,{img_str}" alt="Camera feed" />
            </div>
            '''
            # Store frame in session state to persist across reruns
            st.session_state.last_frame_html = frame_html
            
            # Only update frame if not switching modes (to prevent refresh)
            if not st.session_state.get("switching_mode", False):
                frame_placeholder.markdown(frame_html, unsafe_allow_html=True)
            elif st.session_state.last_frame_html:
                # Keep showing last frame during mode switch
                frame_placeholder.markdown(st.session_state.last_frame_html, unsafe_allow_html=True)

            card_states = compute_card_states(current_detections, now)
            st.session_state.last_card_states = card_states
            
            # Only update if not switching modes (to prevent refresh)
            if not st.session_state.get("switching_mode", False):
                update_side_panels(card_states)
                progress_placeholder.markdown(render_progress_bar(card_states, is_running=True), unsafe_allow_html=True)
            else:
                # Update panels but skip progress bar during mode switch
                update_side_panels(card_states)
    else:
        # Waiting mode - show loading animation only (no camera feed)
        # Only update frame if we don't have a cached one (avoid refresh on mode switch)
        if st.session_state.last_frame_html is None:
            loading_html = f'''
            <div class="camera-container">
                <div class="loading-overlay" style="position:relative;background:transparent;">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Waiting to start detection...</div>
                </div>
            </div>
            '''
            frame_placeholder.markdown(loading_html, unsafe_allow_html=True)
        # If we have a cached frame and are just switching modes, keep showing it
        elif st.session_state.last_frame_html and st.session_state.running == False:
            frame_placeholder.markdown(st.session_state.last_frame_html, unsafe_allow_html=True)
        
        # Update progress bar
        progress_placeholder.markdown(render_progress_bar(is_running=False), unsafe_allow_html=True)
        
        # Always update side panels with last known card states (updates display mode)
        if st.session_state.last_card_states:
            update_side_panels(st.session_state.last_card_states)
        else:
            update_side_panels({})
else:
    st.error("Could not open webcam.")

# Footer
st.markdown(
    "<div style='text-align:center;margin-top:80px;padding:20px;color:#666;font-size:12px;'>"
    "Done by <a href='https://github.com/GhandourGh'>GhandourGh</a> - Using YOLO8"
    "</div>",
    unsafe_allow_html=True,
)
