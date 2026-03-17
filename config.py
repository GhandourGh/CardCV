"""
Configuration constants for the CardCV application.

Defines paths, suit/rank metadata, visual colors, animation timings,
and filename mappings used across the detection and rendering modules.
"""

import os

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
CARDS_DIR = os.path.join(BASE_DIR, "assets", "cards")
MODEL_PATH = os.path.join(BASE_DIR, "models", "playingCards.pt")

# ── Suit metadata ──────────────────────────────────────────────────────────────
# Each suit maps to a Unicode symbol and two colours: a base colour and a
# brighter "glow" variant used for active-detection highlights.
SUITS = {
    "C": {"symbol": "\u2663", "color": "#2e7d32", "glow": "#4caf50"},  # Clubs
    "S": {"symbol": "\u2660", "color": "#1565c0", "glow": "#42a5f5"},  # Spades
    "H": {"symbol": "\u2665", "color": "#c62828", "glow": "#ef5350"},  # Hearts
    "D": {"symbol": "\u2666", "color": "#e65100", "glow": "#ff9800"},  # Diamonds
}

# BGR colours for OpenCV bounding-box drawing (OpenCV uses BGR, not RGB).
SUIT_BGR = {
    "C": (80, 125, 46),
    "S": (192, 101, 21),
    "H": (80, 80, 198),
    "D": (0, 101, 230),
}

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# Numeric values used for the "card sum" feature.
CARD_VALUES = {
    "A": 1, "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 11, "Q": 12, "K": 13,
}

# ── Animation timings ──────────────────────────────────────────────────────────
FADE_DURATION = 0.8   # seconds a card stays visible after leaving the frame
POP_DURATION = 0.35   # seconds for the scale-up animation on first detection

# ── Filename mappings (asset images) ──────────────────────────────────────────
RANK_TO_FILENAME = {
    "A": "ace", "2": "2", "3": "3", "4": "4", "5": "5",
    "6": "6", "7": "7", "8": "8", "9": "9", "10": "10",
    "J": "jack", "Q": "queen", "K": "king",
}
SUIT_TO_FILENAME = {
    "C": "clubs", "S": "spades", "H": "hearts", "D": "diamonds",
}


def suit_key_to_name(key: str) -> str:
    """Convert a single-letter suit key to its full name."""
    return {"C": "Clubs", "S": "Spades", "H": "Hearts", "D": "Diamonds"}[key]
