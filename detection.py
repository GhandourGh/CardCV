"""
Detection module — YOLO model loading, card-image caching, and
state management for tracking which cards are visible, fading, or new.
"""

import base64
import os

import streamlit as st
from ultralytics import YOLO

from config import (
    CARDS_DIR,
    FADE_DURATION,
    MODEL_PATH,
    POP_DURATION,
    RANK_TO_FILENAME,
    SUIT_TO_FILENAME,
)


# ── Model ──────────────────────────────────────────────────────────────────────

@st.cache_resource
def load_model() -> YOLO:
    """Load the YOLOv8 playing-card model (cached across Streamlit reruns)."""
    return YOLO(MODEL_PATH)


# ── Card images ────────────────────────────────────────────────────────────────

@st.cache_data
def load_card_images() -> dict[str, str]:
    """
    Read every card PNG from assets/cards/ and return a dict mapping
    card IDs (e.g. "AH", "10S") to base-64 data-URIs.
    """
    images: dict[str, str] = {}
    for rank_key, rank_name in RANK_TO_FILENAME.items():
        for suit_key, suit_name in SUIT_TO_FILENAME.items():
            card_id = f"{rank_key}{suit_key}"
            filepath = os.path.join(CARDS_DIR, f"{rank_name}_of_{suit_name}.png")
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                images[card_id] = f"data:image/png;base64,{b64}"
    return images


# Pre-load images at import time so they're ready for the renderer.
CARD_IMAGES = load_card_images()


# ── Card state tracking ───────────────────────────────────────────────────────

def compute_card_states(
    current_detections: dict[str, float],
    now: float,
) -> dict[str, tuple[float, bool]]:
    """
    Merge live detections into session history and return a dict of
    card_id → (intensity, is_popping).

    * Newly detected cards get a brief "pop" animation.
    * Cards that leave the frame fade out over ``FADE_DURATION`` seconds.
    * Fully faded cards are removed from history.
    """
    history = st.session_state.card_history

    # Record every card we've ever seen (for the "seen" dimmed state).
    st.session_state.ever_detected.update(current_detections.keys())

    # Update history with current detections.
    for card_id, conf in current_detections.items():
        if card_id not in history or "first_seen" not in history[card_id]:
            history[card_id] = {"conf": conf, "last_seen": now, "first_seen": now}
        else:
            history[card_id]["conf"] = conf
            history[card_id]["last_seen"] = now

    # Build the output states dict.
    states: dict[str, tuple[float, bool]] = {}
    expired: list[str] = []

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
