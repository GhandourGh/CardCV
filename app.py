# Real-time playing card detection using YOLOv8 + Streamlit
#
# Install dependencies:
#   pip install ultralytics opencv-python streamlit
#
# Run:
#   streamlit run app.py

import base64
import os
import time

import cv2
import streamlit as st
from ultralytics import YOLO

SUITS = {
    "C": {"symbol": "\u2663", "color": "#2e7d32", "glow": "#4caf50"},  # Clubs - green
    "S": {"symbol": "\u2660", "color": "#1565c0", "glow": "#42a5f5"},  # Spades - blue
    "H": {"symbol": "\u2665", "color": "#c62828", "glow": "#ef5350"},  # Hearts - red
    "D": {"symbol": "\u2666", "color": "#e65100", "glow": "#ff9800"},  # Diamonds - orange
}

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

SUIT_BGR = {
    "C": (80, 125, 46),   # green
    "S": (192, 101, 21),   # blue
    "H": (80, 80, 198),    # red
    "D": (0, 101, 230),    # orange
}

FADE_DURATION = 0.8  # seconds to fade out after card disappears
POP_DURATION = 0.35  # seconds for the scale-up micro-animation

# --- Card image loading ---
CARDS_DIR = os.path.join(os.path.dirname(__file__), "cards")

RANK_TO_FILENAME = {
    "A": "ace", "2": "2", "3": "3", "4": "4", "5": "5",
    "6": "6", "7": "7", "8": "8", "9": "9", "10": "10",
    "J": "jack", "Q": "queen", "K": "king",
}
SUIT_TO_FILENAME = {"C": "clubs", "S": "spades", "H": "hearts", "D": "diamonds"}


@st.cache_data
def load_card_images():
    """Load all card PNGs as base64 data URIs, keyed by card_id (e.g. 'AH')."""
    images = {}
    for rank_key, rank_name in RANK_TO_FILENAME.items():
        for suit_key, suit_name in SUIT_TO_FILENAME.items():
            card_id = f"{rank_key}{suit_key}"
            filename = f"{rank_name}_of_{suit_name}.png"
            filepath = os.path.join(CARDS_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                images[card_id] = f"data:image/png;base64,{b64}"
    return images


CARD_IMAGES = load_card_images()

CSS_COMMON = """
<style>
@keyframes card-pop {
    0%   { transform: scale(1.0); }
    40%  { transform: scale(1.08); }
    100% { transform: scale(1.0); }
}
.card-grid { display: flex; flex-wrap: wrap; gap: 4px; justify-content: center; margin-bottom: 12px; }
.suit-title { text-align: center; font-size: 18px; font-weight: bold; margin: 8px 0 4px 0; }
.conf-bar {
    position: absolute;
    bottom: 3px; left: 3px;
    height: 3px;
    border-radius: 1px;
    transition: width 0.2s ease;
    z-index: 2;
}
</style>
"""

CSS_ICONS = """
<style>
.card {
    width: 42px; height: 56px;
    border: 2px solid #333;
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: bold;
    background: #1a1a2e;
    color: #555;
    flex-direction: column;
    line-height: 1.1;
    position: relative;
}
.card .rank { font-size: 14px; }
.card .suit { font-size: 12px; }
</style>
"""

CSS_IMAGES = """
<style>
.card {
    width: 52px; height: 73px;
    border: 2px solid #333;
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    background: #1a1a2e;
    position: relative;
    overflow: hidden;
}
.card img {
    width: 100%; height: 100%;
    object-fit: contain;
    border-radius: 4px;
}
.card.dim img {
    filter: brightness(0.15) saturate(0);
}
.card.dim-red img {
    filter: brightness(0.18) saturate(0.4) sepia(0.3) hue-rotate(-10deg);
}
.card.seen img {
    filter: brightness(0.5) saturate(0.3);
}
.card.seen-red img {
    filter: brightness(0.45) saturate(0.5) sepia(0.2) hue-rotate(-10deg);
}
</style>
"""


def _intensity_styles(glow_color, suit_color, intensity):
    """Build inline CSS for a card at a given glow intensity (0.0–1.0).

    intensity drives:
      - box-shadow blur/spread (pulse range scales with intensity)
      - border + text opacity
      - suit symbol color blend toward full color
    """
    # Scale shadow radii by intensity
    r1 = int(6 + 10 * intensity)   # inner glow radius  6..16
    r2 = int(12 + 20 * intensity)  # outer glow radius  12..32
    alpha = round(intensity, 2)

    # Pulse: CSS animation with intensity-scaled shadows baked in
    # We embed a unique @keyframes per card using the intensity value
    anim_name = f"gp{int(intensity * 1000)}"
    lo1, lo2 = int(r1 * 0.6), int(r2 * 0.6)
    hi1, hi2 = r1, r2

    keyframes = (
        f"@keyframes {anim_name} {{"
        f"  0%,100% {{ box-shadow: 0 0 {lo1}px {glow_color}{_hex_alpha(alpha)}, "
        f"0 0 {lo2}px {glow_color}{_hex_alpha(alpha * 0.5)}; }}"
        f"  50% {{ box-shadow: 0 0 {hi1}px {glow_color}{_hex_alpha(alpha)}, "
        f"0 0 {hi2}px {glow_color}{_hex_alpha(alpha * 0.7)}; }}"
        f"}}"
    )

    style = (
        f"border-color: {glow_color}; "
        f"color: rgba(255,255,255,{alpha}); "
        f"background: #1a1a3e; "
    )

    return keyframes, style, alpha, anim_name


def _hex_alpha(a):
    """Convert 0.0–1.0 alpha to 2-char hex suffix (e.g. 0.5 -> '80')."""
    return format(max(0, min(255, int(a * 255))), "02x")


def _suit_header(suit_key, info):
    ever = st.session_state.get("ever_detected", set())
    suit_count = sum(1 for r in RANKS if f"{r}{suit_key}" in ever)
    return f'<div class="suit-title" style="color:{info["color"]}">{info["symbol"]} {suit_key_to_name(suit_key)} ({suit_count}/13)</div>'


def render_suit_icons(suit_key, card_states):
    """Render a suit's 13 cards using text symbols."""
    info = SUITS[suit_key]
    html = CSS_COMMON + CSS_ICONS
    extra_keyframes = ""
    ever = st.session_state.get("ever_detected", set())
    html += _suit_header(suit_key, info)
    html += '<div class="card-grid">'

    for rank in RANKS:
        card_id = f"{rank}{suit_key}"
        state = card_states.get(card_id)

        if state and state[0] > 0.01:
            intensity, is_popping = state
            keyframes, style, alpha, anim_name = _intensity_styles(info["glow"], info["color"], intensity)
            extra_keyframes += keyframes

            if is_popping:
                style += f"animation: {anim_name} 1.8s ease-in-out infinite, card-pop 0.35s ease-out; "
            else:
                style += f"animation: {anim_name} 1.8s ease-in-out infinite; "

            suit_color = info["color"]
            bar_width = int(intensity * 100)
            html += (
                f'<div class="card" style="{style}">'
                f'<span class="rank">{rank}</span>'
                f'<span class="suit" style="color:{suit_color};opacity:{alpha}">{info["symbol"]}</span>'
                f'<div class="conf-bar" style="width:calc({bar_width}% - 6px);background:{info["glow"]}"></div>'
                f'</div>'
            )
        elif card_id in ever:
            html += (
                f'<div class="card" style="border-color:{info["color"]};color:#aaa;background:#151530;">'
                f'<span class="rank">{rank}</span>'
                f'<span class="suit" style="color:{info["color"]};opacity:0.5">{info["symbol"]}</span>'
                f'</div>'
            )
        else:
            html += (
                f'<div class="card">'
                f'<span class="rank">{rank}</span>'
                f'<span class="suit">{info["symbol"]}</span>'
                f'</div>'
            )

    html += '</div>'
    if extra_keyframes:
        html = f"<style>{extra_keyframes}</style>" + html
    return html


def render_suit_images(suit_key, card_states):
    """Render a suit's 13 cards using PNG images."""
    info = SUITS[suit_key]
    is_red = suit_key in ("H", "D")
    html = CSS_COMMON + CSS_IMAGES
    extra_keyframes = ""
    ever = st.session_state.get("ever_detected", set())
    html += _suit_header(suit_key, info)
    html += '<div class="card-grid">'

    for rank in RANKS:
        card_id = f"{rank}{suit_key}"
        img_src = CARD_IMAGES.get(card_id, "")
        state = card_states.get(card_id)

        if state and state[0] > 0.01:
            intensity, is_popping = state
            keyframes, style, alpha, anim_name = _intensity_styles(info["glow"], info["color"], intensity)
            extra_keyframes += keyframes

            if is_popping:
                style += f"animation: {anim_name} 1.8s ease-in-out infinite, card-pop 0.35s ease-out; "
            else:
                style += f"animation: {anim_name} 1.8s ease-in-out infinite; "

            bar_width = int(intensity * 100)
            html += (
                f'<div class="card" style="{style}">'
                f'<img src="{img_src}" alt="{card_id}">'
                f'<div class="conf-bar" style="width:calc({bar_width}% - 4px);background:{info["glow"]}"></div>'
                f'</div>'
            )
        elif card_id in ever:
            seen_cls = "seen-red" if is_red else "seen"
            html += (
                f'<div class="card {seen_cls}" style="border-color:{info["color"]};background:#151530;">'
                f'<img src="{img_src}" alt="{card_id}">'
                f'</div>'
            )
        else:
            dim_cls = "dim-red" if is_red else "dim"
            html += (
                f'<div class="card {dim_cls}">'
                f'<img src="{img_src}" alt="{card_id}">'
                f'</div>'
            )

    html += '</div>'
    if extra_keyframes:
        html = f"<style>{extra_keyframes}</style>" + html
    return html


def suit_key_to_name(key):
    return {"C": "Clubs", "S": "Spades", "H": "Hearts", "D": "Diamonds"}[key]


@st.cache_resource
def load_model():
    return YOLO("playingCards.pt")


st.set_page_config(layout="wide", page_title="Card Detection")

# Hide Streamlit chrome + dark gradient background
st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
.stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #0f0f2e 50%, #0a0a1a 100%);
}
.stMainBlockContainer {
    padding-top: 0px;
}
.stButton > button {
    background: #1a1a3e;
    color: #fff;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 8px 0;
    font-weight: bold;
}
.stButton > button:hover {
    background: #2a2a5e;
    border-color: #555;
    color: #fff;
}
/* Custom toggle switch - From Uiverse.io by Xtenso, adapted for page style */
.filter-switch {
    border: 2px solid #555;
    border-radius: 30px;
    position: relative;
    display: flex;
    align-items: center;
    height: 50px;
    width: 400px;
    overflow: hidden;
    background: #1a1a3e;
    margin: 0 auto;
}
.filter-switch input {
    display: none;
}
.filter-switch label {
    flex: 1;
    text-align: center;
    cursor: pointer;
    border: none;
    border-radius: 30px;
    position: relative;
    overflow: hidden;
    z-index: 1;
    transition: all 0.5s;
    font-weight: 500;
    font-size: 18px;
    padding: 12px 0;
    color: #7d7d7d;
}
.filter-switch .background {
    position: absolute;
    width: 49%;
    height: 38px;
    background-color: #2a2a5e;
    top: 4px;
    left: 4px;
    border-radius: 30px;
    transition: left 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    border: 1px solid #555;
}
#cardOption2:checked ~ .background {
    left: 50%;
}
#cardOption1:checked + label[for="cardOption1"] {
    color: #fff;
    font-weight: bold;
}
#cardOption2:checked + label[for="cardOption2"] {
    color: #fff;
    font-weight: bold;
}
#cardOption1:not(:checked) + label[for="cardOption1"],
#cardOption2:not(:checked) + label[for="cardOption2"] {
    color: #7d7d7d;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;margin-bottom:0'>Playing Card Detection</h2>", unsafe_allow_html=True)

# Card style toggle
if "card_style" not in st.session_state:
    st.session_state.card_style = "Icons"

style_col1, style_col2, style_col3 = st.columns([2, 1, 2])
with style_col2:
    # Create hidden buttons that will be triggered by the toggle
    btn_icons_clicked = st.button("Icons", key="toggle_icons", use_container_width=True)
    if btn_icons_clicked:
        st.session_state.card_style = "Icons"
        st.rerun()
    
    btn_images_clicked = st.button("Images", key="toggle_images", use_container_width=True)
    if btn_images_clicked:
        st.session_state.card_style = "Images"
        st.rerun()
    
    # Hide the Streamlit buttons
    st.markdown("""
    <style>
    button[data-testid*="toggle_icons"],
    button[data-testid*="toggle_images"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Custom toggle switch HTML
    current_index = 0 if st.session_state.card_style == "Icons" else 1
    toggle_html = f"""
    <div id="cardFilter" class="filter-switch">
        <input {'checked=""' if current_index == 0 else ''} id="cardOption1" name="cardOptions" type="radio" />
        <label class="option" for="cardOption1">Icons</label>
        <input {'checked=""' if current_index == 1 else ''} id="cardOption2" name="cardOptions" type="radio" />
        <label class="option" for="cardOption2">Images</label>
        <span class="background"></span>
    </div>
    <script>
    (function() {{
        const option1 = document.getElementById('cardOption1');
        const option2 = document.getElementById('cardOption2');
        
        function findAndClickButton(keyPart) {{
            const buttons = document.querySelectorAll('button[data-testid*="' + keyPart + '"]');
            if (buttons.length > 0) {{
                buttons[0].click();
            }}
        }}
        
        if (option1) {{
            option1.addEventListener('change', function() {{
                if (this.checked) {{
                    setTimeout(() => findAndClickButton('toggle_icons'), 10);
                }}
            }});
            const label1 = document.querySelector('label[for="cardOption1"]');
            if (label1) {{
                label1.style.cursor = 'pointer';
                label1.addEventListener('click', function() {{
                    setTimeout(() => findAndClickButton('toggle_icons'), 50);
                }});
            }}
        }}
        
        if (option2) {{
            option2.addEventListener('change', function() {{
                if (this.checked) {{
                    setTimeout(() => findAndClickButton('toggle_images'), 10);
                }}
            }});
            const label2 = document.querySelector('label[for="cardOption2"]');
            if (label2) {{
                label2.style.cursor = 'pointer';
                label2.addEventListener('click', function() {{
                    setTimeout(() => findAndClickButton('toggle_images'), 50);
                }});
            }}
        }}
    }})();
    </script>
    """
    st.markdown(toggle_html, unsafe_allow_html=True)

card_style = st.session_state.card_style

# Layout: left cards | camera | right cards
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

    st.button(
        "Stop" if st.session_state.running else "Start",
        on_click=toggle,
        use_container_width=True,
    )

# Track last-seen time and confidence per card
if "card_history" not in st.session_state:
    st.session_state.card_history = {}
if "ever_detected" not in st.session_state:
    st.session_state.ever_detected = set()


def compute_card_states(current_detections, now):
    """Return dict of card_id -> (intensity, is_popping).

    current_detections: dict card_id -> confidence (0.0–1.0)
    Handles fade-out for cards that are no longer detected.
    is_popping is True during the first POP_DURATION seconds after detection.
    """
    history = st.session_state.card_history

    # Accumulate ever-detected cards for suit counts and progress bar
    st.session_state.ever_detected.update(current_detections.keys())

    # Update history with current detections
    for card_id, conf in current_detections.items():
        if card_id not in history or "first_seen" not in history[card_id]:
            # New card — record first appearance for pop animation
            history[card_id] = {"conf": conf, "last_seen": now, "first_seen": now}
        else:
            history[card_id]["conf"] = conf
            history[card_id]["last_seen"] = now

    # Build intensity map
    states = {}
    expired = []
    for card_id, info in history.items():
        if card_id in current_detections:
            is_popping = (now - info["first_seen"]) < POP_DURATION
            states[card_id] = (info["conf"], is_popping)
        else:
            # Fading: intensity decays from last confidence over FADE_DURATION
            elapsed = now - info["last_seen"]
            if elapsed < FADE_DURATION:
                fade = 1.0 - (elapsed / FADE_DURATION)
                states[card_id] = (info["conf"] * fade, False)
            else:
                expired.append(card_id)

    # Clean up fully faded cards (also resets first_seen so next detection pops again)
    for card_id in expired:
        del history[card_id]

    return states


SUIT_DIVIDER = '<hr style="border:none;border-top:1px solid #333;margin:12px 0;">'


def render_progress_bar():
    count = len(st.session_state.get("ever_detected", set()))
    pct = int(count / 52 * 100)
    return f'''
    <div style="background:#1a1a2e;border-radius:8px;height:28px;position:relative;
                border:1px solid #333;margin-bottom:8px;overflow:hidden;">
        <div style="width:{pct}%;height:100%;border-radius:7px;
                    background:linear-gradient(90deg,#2e7d32,#1565c0);
                    transition:width 0.3s ease;"></div>
        <span style="position:absolute;top:0;left:0;right:0;bottom:0;
                     display:flex;align-items:center;justify-content:center;
                     color:#fff;font-size:13px;font-weight:bold;">
            {count} / 52 detected
        </span>
    </div>'''


def update_side_panels(card_states):
    render = render_suit_images if st.session_state.card_style == "Images" else render_suit_icons
    left_html = render("C", card_states) + SUIT_DIVIDER + render("S", card_states)
    right_html = render("H", card_states) + SUIT_DIVIDER + render("D", card_states)
    left_placeholder.markdown(left_html, unsafe_allow_html=True)
    right_placeholder.markdown(right_html, unsafe_allow_html=True)


# Show cards and progress bar in default state
update_side_panels({})
progress_placeholder.markdown(render_progress_bar(), unsafe_allow_html=True)

if st.session_state.running:
    model = load_model()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        st.error("Could not open webcam.")
    else:
        while st.session_state.running:
            ret, frame = cap.read()
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

                # Keep highest confidence if same card detected multiple times
                if name not in current_detections or conf > current_detections[name]:
                    current_detections[name] = conf

                box_color = SUIT_BGR.get(name[-1], (0, 255, 0))
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

            card_states = compute_card_states(current_detections, now)
            update_side_panels(card_states)
            progress_placeholder.markdown(render_progress_bar(), unsafe_allow_html=True)

        cap.release()
