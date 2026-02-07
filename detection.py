import base64
import os

import streamlit as st
from ultralytics import YOLO

from config import (
    CARDS_DIR, MODEL_PATH, RANK_TO_FILENAME, SUIT_TO_FILENAME,
    FADE_DURATION, POP_DURATION,
)


@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)


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


def compute_card_states(current_detections, now):
    """Return dict of card_id -> (intensity, is_popping).

    current_detections: dict card_id -> confidence (0.0-1.0)
    Handles fade-out for cards that are no longer detected.
    is_popping is True during the first POP_DURATION seconds after detection.
    """
    history = st.session_state.card_history

    st.session_state.ever_detected.update(current_detections.keys())

    for card_id, conf in current_detections.items():
        if card_id not in history or "first_seen" not in history[card_id]:
            history[card_id] = {"conf": conf, "last_seen": now, "first_seen": now}
        else:
            history[card_id]["conf"] = conf
            history[card_id]["last_seen"] = now

    states = {}
    expired = []
    for card_id, info in history.items():
        if card_id in current_detections:
            is_popping = (now - info["first_seen"]) < POP_DURATION
            states[card_id] = (info["conf"], is_popping)
        else:
            elapsed = now - info["last_seen"]
            if elapsed < FADE_DURATION:
                fade = 1.0 - (elapsed / FADE_DURATION)
                states[card_id] = (info["conf"] * fade, False)
            else:
                expired.append(card_id)

    for card_id in expired:
        del history[card_id]

    return states
