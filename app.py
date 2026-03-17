"""
CardCV — Real-time playing card detection powered by YOLOv8.

This is the main Streamlit application. It opens a webcam feed, runs
YOLOv8 inference on every frame, draws colour-coded bounding boxes,
and displays an interactive card grid in the sidebar.

Run with:  streamlit run app.py
"""

import base64
import io
import sys
import time
import logging

# ── Suppress noisy warnings before any library imports ─────────────────────────
logging.getLogger().setLevel(logging.CRITICAL)

_stderr = sys.stderr

class _FilterStderr:
    """Filter out macOS camera deprecation warnings from stderr."""
    _SUPPRESS = ("AVCaptureDeviceTypeExternal", "Continuity Camera",
                 "NSCameraUseContinuityCameraDeviceType")

    def write(self, msg):
        if any(kw in str(msg) for kw in self._SUPPRESS):
            return
        _stderr.write(msg)

    def flush(self):
        _stderr.flush()

    def __getattr__(self, name):
        return getattr(_stderr, name)

sys.stderr = _FilterStderr()

# ── Third-party imports ────────────────────────────────────────────────────────
import cv2
import streamlit as st
from PIL import Image

try:
    from streamlit_extras.badges import badge
except ImportError:
    badge = None

# ── Local imports ──────────────────────────────────────────────────────────────
from config import SUIT_BGR
from detection import compute_card_states, load_model
from renderer import (
    render_card_sum,
    render_info_panel,
    render_progress_bar,
    render_suit_icons,
    render_suit_images,
)
from styles import PAGE_CSS, SUIT_DIVIDER


# ═══════════════════════════════════════════════════════════════════════════════
#  Camera management
# ═══════════════════════════════════════════════════════════════════════════════

# Kept at module level (outside st.session_state) to avoid Streamlit
# serialisation issues that can cause segfaults on hot-reload.
_camera: dict = {"cap": None}


def _get_camera() -> cv2.VideoCapture | None:
    """Open (or reuse) the default webcam."""
    if _camera["cap"] is None or not _camera["cap"].isOpened():
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        _camera["cap"] = cap
    return _camera["cap"]


def _release_camera() -> None:
    """Release the webcam if it's open."""
    if _camera["cap"] is not None:
        _camera["cap"].release()
        _camera["cap"] = None


def _frame_to_base64(frame_rgb) -> str:
    """Convert an RGB numpy frame to a JPEG base-64 string."""
    buf = io.BytesIO()
    Image.fromarray(frame_rgb).save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


# ═══════════════════════════════════════════════════════════════════════════════
#  Page setup
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(layout="wide", page_title="Card Detection")
st.markdown(PAGE_CSS, unsafe_allow_html=True)

st.markdown(
    '<div style="text-align:center;margin-bottom:8px;padding:8px 0;">'
    '<h1 style="font-size:1.5rem;font-weight:700;color:hsl(210 40% 98%);'
    'margin:0 0 4px 0;letter-spacing:-0.025em;">Playing Card Detection</h1>'
    '<p style="font-size:0.8rem;color:hsl(217.9 10.6% 64.9%);margin:0;">'
    'Real-time card recognition powered by '
    '<strong style="color:hsl(221.2 83.2% 53.3%);">YOLOv8</strong></p></div>',
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  Session state defaults
# ═══════════════════════════════════════════════════════════════════════════════

_DEFAULTS = {
    "card_style": "Icons",
    "switching_mode": False,
    "running": False,
    "card_history": {},
    "ever_detected": set(),
    "last_frame_html": None,
    "last_card_states": {},
    "cached_icons_html": {"left": "", "right": ""},
    "cached_images_html": {"left": "", "right": ""},
}
for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ═══════════════════════════════════════════════════════════════════════════════
#  Layout — three-column: left cards | camera | right cards
# ═══════════════════════════════════════════════════════════════════════════════

left_col, center_col, right_col = st.columns([1, 2, 1])

with left_col:
    left_placeholder = st.empty()
with right_col:
    right_placeholder = st.empty()
with center_col:
    progress_placeholder = st.empty()
    frame_placeholder = st.empty()
    sum_placeholder = st.empty()

    # ── Control callbacks ──────────────────────────────────────────────────

    def _toggle_detection():
        st.session_state.running = not st.session_state.running
        if not st.session_state.running:
            st.session_state.last_frame_html = None

    def _set_style(style: str):
        if st.session_state.card_style == style:
            return
        st.session_state.switching_mode = True
        st.session_state.card_style = style
        # Apply cached HTML if available for an instant visual switch.
        cache_key = "cached_icons_html" if style == "Icons" else "cached_images_html"
        cached = st.session_state[cache_key]
        if cached["left"]:
            left_placeholder.markdown(cached["left"], unsafe_allow_html=True)
            right_placeholder.markdown(cached["right"], unsafe_allow_html=True)
        elif st.session_state.last_card_states:
            _update_side_panels(st.session_state.last_card_states)

    # ── Style toggle buttons ──────────────────────────────────────────────
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    icon_col, image_col = st.columns(2)
    with icon_col:
        st.button(
            "Icons", on_click=_set_style, args=("Icons",),
            use_container_width=True,
            type="primary" if st.session_state.card_style == "Icons" else "secondary",
        )
    with image_col:
        st.button(
            "Images", on_click=_set_style, args=("Images",),
            use_container_width=True,
            type="primary" if st.session_state.card_style == "Images" else "secondary",
        )

    # ── Start / Stop button ───────────────────────────────────────────────
    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
    st.button(
        "Stop Detection" if st.session_state.running else "Start Detection",
        on_click=_toggle_detection,
        use_container_width=True,
        type="primary",
    )

    status = "Running" if st.session_state.running else "Idle"
    st.caption(f"{'⚡' if st.session_state.running else '⏸'} {status}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Side-panel update helper
# ═══════════════════════════════════════════════════════════════════════════════

def _update_side_panels(card_states: dict) -> None:
    """Re-render the left (Clubs+Spades) and right (Hearts+Diamonds) panels."""
    render = render_suit_images if st.session_state.card_style == "Images" else render_suit_icons
    left_html = render("C", card_states) + SUIT_DIVIDER + render("S", card_states)
    right_html = render("H", card_states) + SUIT_DIVIDER + render("D", card_states)

    # Cache for instant switching between icon/image modes.
    cache_key = "cached_icons_html" if st.session_state.card_style == "Icons" else "cached_images_html"
    st.session_state[cache_key] = {"left": left_html, "right": right_html}

    left_placeholder.markdown(left_html, unsafe_allow_html=True)
    right_placeholder.markdown(right_html, unsafe_allow_html=True)

    if st.session_state.get("switching_mode"):
        st.session_state.switching_mode = False


# Initialise panels on first load (or when detection is stopped).
if not st.session_state.get("switching_mode"):
    if not st.session_state.last_card_states:
        _update_side_panels({})
        progress_placeholder.markdown(render_progress_bar(is_running=False), unsafe_allow_html=True)
    else:
        _update_side_panels(st.session_state.last_card_states)
        if not st.session_state.running:
            progress_placeholder.markdown(
                render_progress_bar(st.session_state.last_card_states, is_running=False),
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
#  Main detection loop
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.running:
    cap = _get_camera()

    if cap is not None and cap.isOpened():
        model = load_model()

        while st.session_state.running:
            ret, frame = cap.read()
            if not ret:
                st.warning("Lost webcam feed.")
                break

            # Run YOLO inference on the frame.
            results = model(frame, imgsz=320, conf=0.85, verbose=False)
            now = time.time()

            # Collect the best confidence for each detected card.
            current_detections: dict[str, float] = {}
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls_id = int(box.cls[0])
                name = model.names[cls_id]
                conf = float(box.conf[0])

                if name not in current_detections or conf > current_detections[name]:
                    current_detections[name] = conf

                # Draw a colour-coded bounding box.
                color = SUIT_BGR.get(name[-1], (0, 255, 0))
                label = f"{name} ({int(conf * 100)}%)"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Convert the annotated frame to base-64 for display.
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_str = _frame_to_base64(frame_rgb)
            frame_html = (
                '<div class="camera-container">'
                f'<img src="data:image/jpeg;base64,{img_str}" alt="Camera feed" />'
                '</div>'
            )
            st.session_state.last_frame_html = frame_html

            # Update the UI (skip frame refresh during a mode switch).
            switching = st.session_state.get("switching_mode", False)
            if not switching:
                frame_placeholder.markdown(frame_html, unsafe_allow_html=True)
            elif st.session_state.last_frame_html:
                frame_placeholder.markdown(st.session_state.last_frame_html, unsafe_allow_html=True)

            card_states = compute_card_states(current_detections, now)
            st.session_state.last_card_states = card_states

            if not switching:
                _update_side_panels(card_states)
                progress_placeholder.markdown(
                    render_progress_bar(card_states, is_running=True), unsafe_allow_html=True,
                )
                sum_placeholder.markdown(render_card_sum(current_detections), unsafe_allow_html=True)
            else:
                _update_side_panels(card_states)
    else:
        st.error("Could not open webcam.")

else:
    # Detection stopped — release the camera.
    _release_camera()

    frame_placeholder.markdown(
        '<div class="camera-container">'
        '<div class="loading-overlay" style="position:relative;background:transparent;">'
        '<div class="loading-spinner"></div>'
        '<div class="loading-text">Waiting to start detection...</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    sum_placeholder.markdown(render_card_sum({}), unsafe_allow_html=True)
    progress_placeholder.markdown(render_progress_bar(is_running=False), unsafe_allow_html=True)
    _update_side_panels(st.session_state.get("last_card_states", {}) or {})


# ═══════════════════════════════════════════════════════════════════════════════
#  Footer & info panels
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(
    "<div style='text-align:center;margin-top:20px;padding:12px;color:#666;font-size:12px;'>"
    "Done by <a href='https://github.com/GhandourGh'>GhandourGh</a> — Using YOLOv8"
    "</div>",
    unsafe_allow_html=True,
)

info_left_col, info_right_col = st.columns(2)
with info_left_col:
    with st.expander("About This Project"):
        st.markdown(render_info_panel("left"), unsafe_allow_html=True)
with info_right_col:
    with st.expander("Detection Legend"):
        st.markdown(render_info_panel("right"), unsafe_allow_html=True)
