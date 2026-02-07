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

PAGE_CSS = """
<style>
#MainMenu, footer, header { visibility: hidden; }
.stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #0f0f2e 50%, #0a0a1a 100%);
}
.stMainBlockContainer {
    padding-top: 0px;
}
/* Modern shadcn/TailwindUI-inspired buttons */
.stButton > button {
    background: hsl(222.2 84% 4.9%);
    color: hsl(210 40% 98%);
    border: 1px solid hsl(217.2 32.6% 17.5%);
    border-radius: calc(0.5rem - 2px);
    padding: 0.625rem 1.25rem;
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}
.stButton > button:hover {
    background: hsl(222.2 47.4% 11.2%);
    border-color: hsl(217.2 32.6% 17.5%);
    color: hsl(210 40% 98%);
    transform: translateY(-1px);
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
}
.stButton > button:active {
    transform: translateY(0);
}
/* Primary button variant */
button[kind="primary"],
.stButton[kind="primary"] > button {
    background: hsl(221.2 83.2% 53.3%);
    color: white;
    border-color: hsl(221.2 83.2% 53.3%);
}
button[kind="primary"]:hover,
.stButton[kind="primary"] > button:hover {
    background: hsl(221.2 83.2% 53.3% / 0.9);
    border-color: hsl(221.2 83.2% 53.3%);
}
/* Toggle button group styles */
.toggle-group {
    display: inline-flex;
    border-radius: calc(0.5rem - 2px);
    background: hsl(222.2 84% 4.9%);
    border: 1px solid hsl(217.2 32.6% 17.5%);
    padding: 2px;
    gap: 2px;
}
.toggle-item {
    padding: 0.5rem 1rem;
    border-radius: calc(0.5rem - 4px);
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s;
    cursor: pointer;
    border: none;
    background: transparent;
    color: hsl(217.9 10.6% 64.9%);
}
.toggle-item:hover {
    background: hsl(217.2 32.6% 17.5%);
    color: hsl(210 40% 98%);
}
.toggle-item.active {
    background: hsl(222.2 47.4% 11.2%);
    color: hsl(210 40% 98%);
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}
@keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 0.8; }
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}
.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(10, 10, 26, 0.85);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    z-index: 10;
}
.loading-spinner {
    width: 50px;
    height: 50px;
    border: 4px solid rgba(255, 255, 255, 0.1);
    border-top: 4px solid #42a5f5;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 15px;
}
.loading-text {
    color: #fff;
    font-size: 16px;
    font-weight: bold;
    animation: pulse 2s ease-in-out infinite;
}
.camera-container {
    position: relative;
    border-radius: 8px;
    overflow: hidden;
    width: 100%;
    aspect-ratio: 4 / 3;
    background: #1a1a2e;
    border: 1px solid #333;
    display: flex;
    align-items: center;
    justify-content: center;
}
.camera-container img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}
</style>
"""

SUIT_DIVIDER = '<hr style="border:none;border-top:1px solid #333;margin:12px 0;">'
