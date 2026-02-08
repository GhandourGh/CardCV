import os

BASE_DIR = os.path.dirname(__file__)
CARDS_DIR = os.path.join(BASE_DIR, "assets", "cards")
MODEL_PATH = os.path.join(BASE_DIR, "models", "playingCards.pt")

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

FADE_DURATION = 0.8   # seconds to fade out after card disappears
POP_DURATION = 0.35   # seconds for the scale-up micro-animation

CARD_VALUES = {
    "A": 1, "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 11, "Q": 12, "K": 13,
}

RANK_TO_FILENAME = {
    "A": "ace", "2": "2", "3": "3", "4": "4", "5": "5",
    "6": "6", "7": "7", "8": "8", "9": "9", "10": "10",
    "J": "jack", "Q": "queen", "K": "king",
}
SUIT_TO_FILENAME = {"C": "clubs", "S": "spades", "H": "hearts", "D": "diamonds"}


def suit_key_to_name(key):
    return {"C": "Clubs", "S": "Spades", "H": "Hearts", "D": "Diamonds"}[key]
