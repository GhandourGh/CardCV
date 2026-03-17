#!/usr/bin/env python3
"""
Convenience launcher for the CardCV Streamlit application.

Usage:
    python run_app.py
"""

import sys
import warnings

# Suppress noisy warnings (hashlib blake2 on some macOS Python builds).
warnings.filterwarnings("ignore")

import streamlit.web.cli as stcli

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app.py"] + sys.argv[1:]
    sys.exit(stcli.main())
