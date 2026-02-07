import streamlit as st

from config import SUITS, RANKS, suit_key_to_name
from detection import CARD_IMAGES
from styles import CSS_COMMON, CSS_ICONS, CSS_IMAGES


def _hex_alpha(a):
    """Convert 0.0-1.0 alpha to 2-char hex suffix (e.g. 0.5 -> '80')."""
    return format(max(0, min(255, int(a * 255))), "02x")


def _intensity_styles(glow_color, intensity):
    """Build inline CSS for a card at a given glow intensity (0.0-1.0)."""
    r1 = int(6 + 10 * intensity)
    r2 = int(12 + 20 * intensity)
    alpha = round(intensity, 2)

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


def _suit_header(suit_key, info):
    ever = st.session_state.get("ever_detected", set())
    suit_count = sum(1 for r in RANKS if f"{r}{suit_key}" in ever)
    return (
        f'<div class="suit-title" style="color:{info["color"]}">'
        f'{info["symbol"]} {suit_key_to_name(suit_key)} ({suit_count}/13)</div>'
    )


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
            keyframes, style, alpha, anim_name = _intensity_styles(info["glow"], intensity)
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
            keyframes, style, alpha, anim_name = _intensity_styles(info["glow"], intensity)
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


def render_info_panel(side="left"):
    """Render info panels above the card grids."""
    # Shared styles
    box = "background:#12122a;border-radius:10px;padding:20px;margin-bottom:16px;border:1px solid #252550;"

    # Heroicons (outline, 24x24) — using currentColor for stroke
    ico_viewfinder = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7.5 3.75H6C4.757 3.75 3.75 4.757 3.75 6V7.5M16.5 3.75H18C19.243 3.75 20.25 4.757 20.25 6V7.5M20.25 16.5V18C20.25 19.243 19.243 20.25 18 20.25H16.5M7.5 20.25H6C4.757 20.25 3.75 19.243 3.75 18V16.5M15 12A3 3 0 1 1 9 12 3 3 0 0 1 15 12Z"/></svg>'
    ico_camera = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6.827 6.175A2.25 2.25 0 0 1 5.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18A2.25 2.25 0 0 0 4.5 20.25h15A2.25 2.25 0 0 0 21.75 18V9.574c0-1.067-.749-1.994-1.802-2.169a47 47 0 0 0-1.134-.175 2.25 2.25 0 0 1-1.641-1.056l-.821-1.316A2.25 2.25 0 0 0 14.616 3.82 48 48 0 0 0 12 3.75c-.878 0-1.75.024-2.616.07a2.25 2.25 0 0 0-1.909 1.039l-.648 1.316Z"/><path d="M16.5 12.75a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0Z"/></svg>'
    ico_chip = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8.25 3V4.5M4.5 8.25H3M21 8.25h-1.5M4.5 12H3m18 0h-1.5M4.5 15.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18V4.5m0 15V21M6.75 19.5h10.5A2.25 2.25 0 0 0 19.5 17.25V6.75A2.25 2.25 0 0 0 17.25 4.5H6.75A2.25 2.25 0 0 0 4.5 6.75v10.5A2.25 2.25 0 0 0 6.75 19.5ZM7.5 7.5h9v9h-9v-9Z"/></svg>'
    ico_bolt = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.75 13.5 14.25 2.25 12 10.5h8.25L9.75 21.75 12 13.5H3.75Z"/></svg>'
    ico_chart = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.125A1.125 1.125 0 0 1 4.125 12h2.25A1.125 1.125 0 0 1 7.5 13.125v6.75A1.125 1.125 0 0 1 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75Z"/><path d="M9.75 8.625A1.125 1.125 0 0 1 10.875 7.5h2.25a1.125 1.125 0 0 1 1.125 1.125v11.25A1.125 1.125 0 0 1 13.125 21h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625Z"/><path d="M16.5 4.125A1.125 1.125 0 0 1 17.625 3h2.25A1.125 1.125 0 0 1 21 4.125v15.75A1.125 1.125 0 0 1 19.875 21h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"/></svg>'
    ico_sun = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-2.227-1.591 1.591M5.25 12H3m2.227-4.773L3.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z"/></svg>'
    ico_eye = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2.036 12.322A10.46 10.46 0 0 1 12 4.5c4.639 0 8.574 3.007 9.964 7.178a.48.48 0 0 1-.07.639A10.46 10.46 0 0 1 12 19.5c-4.638 0-8.574-3.007-9.964-7.178Z"/><path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/></svg>'
    ico_stack = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6.878V6a2.25 2.25 0 0 1 2.25-2.25h7.5A2.25 2.25 0 0 1 18 6v.878m-12 0c.235-.083.487-.128.75-.128h10.5c.263 0 .515.045.75.128M6 6.878A2.25 2.25 0 0 0 4.5 9v.878m13.5-3A2.25 2.25 0 0 1 19.5 9v.878m0 0A1.76 1.76 0 0 0 18.75 9.75H5.25c-.263 0-.515.045-.75.128M19.5 9.878A2.25 2.25 0 0 1 21 12v6a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 18v-6a2.25 2.25 0 0 1 1.5-2.122"/></svg>'

    if side == "left":
        return f'''
<div style="{box}">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
    <div style="width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#1565c0,#42a5f5);
                display:flex;align-items:center;justify-content:center;flex-shrink:0;color:#fff;">{ico_viewfinder}</div>
    <div style="font-size:17px;font-weight:700;color:#e0e0e0;">About This Project</div>
  </div>
  <div style="color:#b0b0c0;font-size:14px;line-height:1.7;margin-bottom:16px;">
    Real-time playing card detection powered by
    <span style="color:#42a5f5;font-weight:600;">YOLOv8</span> deep learning.
    Identifies all 52 standard cards through your webcam.
  </div>
  <div style="border-top:1px solid #252550;padding-top:14px;">
    <div style="font-size:15px;font-weight:600;color:#c0c0d0;margin-bottom:12px;">How It Works</div>
    <div style="display:flex;flex-direction:column;gap:10px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:28px;height:28px;border-radius:6px;background:#1a2a4e;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:#42a5f5;">
          {ico_camera}</div>
        <span style="color:#b0b0c0;font-size:13px;">Captures video frames from webcam</span>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:28px;height:28px;border-radius:6px;background:#1a2a4e;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:#ab47bc;">
          {ico_chip}</div>
        <span style="color:#b0b0c0;font-size:13px;">YOLOv8 detects cards with confidence</span>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:28px;height:28px;border-radius:6px;background:#1a2a4e;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:#ffca28;">
          {ico_bolt}</div>
        <span style="color:#b0b0c0;font-size:13px;">Cards light up in real-time as detected</span>
      </div>
    </div>
  </div>
  <div style="border-top:1px solid #252550;margin-top:14px;padding-top:14px;">
    <div style="font-size:15px;font-weight:600;color:#c0c0d0;margin-bottom:10px;">Tech Stack</div>
    <div style="display:flex;flex-wrap:wrap;gap:6px;">
      <span style="background:#1a2a4e;color:#42a5f5;font-size:12px;font-weight:600;padding:4px 10px;border-radius:20px;">YOLOv8</span>
      <span style="background:#1a2a4e;color:#4caf50;font-size:12px;font-weight:600;padding:4px 10px;border-radius:20px;">OpenCV</span>
      <span style="background:#1a2a4e;color:#ef5350;font-size:12px;font-weight:600;padding:4px 10px;border-radius:20px;">Streamlit</span>
      <span style="background:#1a2a4e;color:#ff9800;font-size:12px;font-weight:600;padding:4px 10px;border-radius:20px;">Ultralytics</span>
    </div>
  </div>
</div>'''

    # Right side — Legend + Tips
    return f'''
<div style="{box}">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
    <div style="width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#c62828,#ef5350);
                display:flex;align-items:center;justify-content:center;flex-shrink:0;color:#fff;">{ico_chart}</div>
    <div style="font-size:17px;font-weight:700;color:#e0e0e0;">Detection Legend</div>
  </div>
  <div style="display:flex;flex-direction:column;gap:12px;margin-bottom:16px;">
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="width:40px;height:28px;border:2px solid #4caf50;border-radius:5px;background:#1a1a3e;
                  box-shadow:0 0 8px #4caf5060;position:relative;flex-shrink:0;">
        <div style="position:absolute;bottom:2px;left:3px;right:3px;height:3px;background:#4caf50;border-radius:1px;"></div>
      </div>
      <div>
        <div style="color:#4caf50;font-size:14px;font-weight:600;">Active</div>
        <div style="color:#888;font-size:12px;">Currently in frame</div>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="width:40px;height:28px;border:2px solid #1565c0;border-radius:5px;background:#151530;flex-shrink:0;"></div>
      <div>
        <div style="color:#42a5f5;font-size:14px;font-weight:600;">Seen</div>
        <div style="color:#888;font-size:12px;">Previously detected</div>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="width:40px;height:28px;border:2px solid #333;border-radius:5px;background:#1a1a2e;flex-shrink:0;"></div>
      <div>
        <div style="color:#666;font-size:14px;font-weight:600;">Unknown</div>
        <div style="color:#888;font-size:12px;">Not yet detected</div>
      </div>
    </div>
  </div>
  <div style="border-top:1px solid #252550;padding-top:14px;margin-bottom:14px;">
    <div style="font-size:15px;font-weight:600;color:#c0c0d0;margin-bottom:10px;">Tips</div>
    <div style="display:flex;flex-direction:column;gap:8px;">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="color:#ff9800;display:flex;">{ico_sun}</span>
        <span style="color:#b0b0c0;font-size:13px;">Good lighting helps accuracy</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="color:#42a5f5;display:flex;">{ico_eye}</span>
        <span style="color:#b0b0c0;font-size:13px;">Hold cards flat and facing camera</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="color:#4caf50;display:flex;">{ico_stack}</span>
        <span style="color:#b0b0c0;font-size:13px;">One card at a time works best</span>
      </div>
    </div>
  </div>
</div>'''


def render_progress_bar(card_states=None, is_running=False):
    """Render progress bar with dynamic status text.
    
    Args:
        card_states: dict of card_id -> (intensity, is_popping) or None
        is_running: whether detection is currently running
    """
    count = len(st.session_state.get("ever_detected", set()))
    pct = int(count / 52 * 100)
    
    # Determine status message
    if not is_running:
        status = "Waiting for cards…"
    elif not card_states or not any(state and state[0] > 0.01 for state in card_states.values()):
        status = "Detecting…"
    else:
        # Calculate average confidence from active detections
        active_confidences = [state[0] for state in card_states.values() if state and state[0] > 0.01]
        if active_confidences:
            avg_confidence = sum(active_confidences) / len(active_confidences)
            if avg_confidence < 0.7:
                status = "Low confidence – adjust lighting"
            else:
                status = "Stable detection"
        else:
            status = "Detecting…"
    
    return f'''
    <div style="background:#1a1a2e;border-radius:8px;height:28px;position:relative;
                border:1px solid #333;margin-bottom:8px;overflow:hidden;">
        <div style="width:{pct}%;height:100%;border-radius:7px;
                    background:linear-gradient(90deg,#2e7d32,#1565c0);
                    transition:width 0.3s ease;"></div>
        <span style="position:absolute;top:0;left:0;right:0;bottom:0;
                     display:flex;align-items:center;justify-content:center;
                     color:#fff;font-size:13px;font-weight:bold;">
            {count} / 52 detected • {status}
        </span>
    </div>'''


