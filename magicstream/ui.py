"""
================================================================================
MagicStream UI & Styling Engine: Cyberpunk Terminal Design System
Author: Shubham Kumar Jha
License: MIT
================================================================================
High-performance ANSI & TrueColor terminal styling, pixel-perfect box rendering,
Unicode width calculations, and dynamic hardware diagnostic cards.
"""

import os
import re
import sys
import unicodedata
from typing import Optional, Dict, Any

# ------------------------------------------------------------------------------
# ANSI & TRUECOLOR COLOR PALETTE
# ------------------------------------------------------------------------------
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
ITALIC  = "\033[3m"

# Standard Neon ANSI Colors
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"

ANSI_REGEX = re.compile(r"\033\[[0-9;]*m")

# Check if terminal supports 24-bit TrueColor
SUPPORTS_TRUECOLOR = os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit") or \
                     "xterm-256color" in os.environ.get("TERM", "") or \
                     not sys.platform.startswith("win")


def rgb(r: int, g: int, b: int) -> str:
    """Returns 24-bit TrueColor ANSI escape sequence."""
    if SUPPORTS_TRUECOLOR:
        return f"\033[38;2;{r};{g};{b}m"
    return CYAN


def char_width(c: str) -> int:
    """Accurately calculates display column width of a single character in monospaced terminal."""
    o = ord(c)
    # Zero-width characters (variation selectors, combining marks)
    if o in (0xFE0E, 0xFE0F):
        return 0
    if unicodedata.combining(c):
        return 0
    # Miscellaneous symbols, pictographs, emojis (rendered as 2 columns)
    if 0x1F300 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF:
        return 2
    # East Asian Wide or Fullwidth
    if unicodedata.east_asian_width(c) in ("W", "F"):
        return 2
    return 1


def term_width(s: str) -> int:
    """Calculates true terminal column width of string, ignoring ANSI codes."""
    clean = ANSI_REGEX.sub("", s)
    return sum(char_width(c) for c in clean)


# Box sizing configured for standard 80-column terminal compatibility
BOX_TOTAL = 78
BOX_INNER = 76
BOX_CONTENT = 72


def get_banner() -> str:
    """Returns vibrant gradient ASCII art banner for MagicStream."""
    raw_lines = [
        r"  __  __             _      ____  _                              ",
        r" |  \/  | __ _  __ _(_) ___/ ___|| |_ _ __ ___  __ _ _ __ ___   ",
        r" | |\/| |/ _` |/ _` | |/ __\___ \| __| '__/ _ \/ _` | '_ ` _ \  ",
        r" | |  | | (_| | (_| | | (__ ___) | |_| | |  __/ (_| | | | | | | ",
        r" |_|  |_|\__,_|\__, |_|\___|____/ \__|_|  \___|\__,_|_| |_| |_| ",
        r"               |___/                                            ",
    ]

    stops = [
        (0, 245, 255),    # Vibrant Electric Cyan
        (30, 180, 255),   # Sky Blue
        (110, 110, 255),  # Royal Blue / Indigo
        (185, 60, 255),   # Electric Purple Neon
        (245, 50, 195),   # Hot Pink / Magenta
        (255, 80, 130),   # Sunset Coral
    ]

    out = [""]
    for idx, line in enumerate(raw_lines):
        r, g, b = stops[idx]
        out.append(f"{BOLD}{rgb(r, g, b)}{line}{RESET}")

    out.append(f"  {CYAN}⚡ {BOLD}24/7 MULTI-PLATFORM LIVE BROADCAST STUDIO{RESET}{CYAN} ⚡{RESET}")
    out.append(f"  {YELLOW}>> Crafted with {RED}❤️{YELLOW} by {BOLD}Shubham Kumar Jha{RESET}{YELLOW} | {WHITE}MIT License{YELLOW} | {GREEN}v2.0.0 Stable{YELLOW} <<{RESET}\n")
    return "\n".join(out)


def render_box_top(title: str = "", tag: str = "", border_color: str = CYAN) -> str:
    """Renders top border of rounded box: ╭─── [ Title ] ────────── [ Tag ] ───╮"""
    t_str = f" [ {BOLD}{WHITE}{title}{RESET}{border_color} ] " if title else ""
    tag_str = f" [ {tag}{RESET}{border_color} ] " if tag else ""
    t_w = term_width(t_str)
    tag_w = term_width(tag_str)
    dash_avail = max(0, BOX_INNER - t_w - tag_w)
    left = 3
    right = max(1, dash_avail - left)
    return f"{border_color}╭{'─' * left}{t_str}{'─' * right}{tag_str}╮{RESET}"


def render_box_line(content: str, border_color: str = CYAN) -> str:
    """Renders a single content line with pixel-perfect padding inside the box: │  Content  │"""
    w = term_width(content)
    pad = " " * max(0, BOX_CONTENT - w)
    return f"{border_color}│{RESET}  {content}{pad}  {border_color}│{RESET}"


def render_box_separator(title: str = "", border_color: str = CYAN) -> str:
    """Renders a middle horizontal dividing line: ├─── [ Section ] ────────┤"""
    if not title:
        return f"{border_color}├{'─' * BOX_INNER}┤{RESET}"
    t_str = f" [ {BOLD}{WHITE}{title}{RESET}{border_color} ] "
    t_w = term_width(t_str)
    dash_avail = max(0, BOX_INNER - t_w)
    left = 3
    right = max(1, dash_avail - left)
    return f"{border_color}├{'─' * left}{t_str}{'─' * right}┤{RESET}"


def render_box_bottom(border_color: str = CYAN) -> str:
    """Renders bottom border of rounded box: ╰────────────────────────────╯"""
    return f"{border_color}╰{'─' * BOX_INNER}╯{RESET}"


def mini_progress_bar(val: float, max_val: float, width: int = 12, color: str = GREEN) -> str:
    """Generates an aesthetic block progress bar: [████████░░░░]"""
    pct = min(1.0, max(0.0, val / max(1.0, max_val)))
    filled = int(round(pct * width))
    empty = width - filled
    return f"{color}{'█' * filled}{DIM}{'░' * empty}{RESET}"


def render_hardware_card(
    hw: Dict[str, Any],
    encoder: str = "libopenh264",
    log_path: str = "logs/stream.log",
    border_color: str = CYAN
) -> str:
    """
    Renders the state-of-the-art hardware diagnostics and adaptive profile card.
    Replaces old plain double-border boxes with modern cyberpunk styling.
    """
    ram_mb = hw.get("ram_mb", 0)
    ram_gb = hw.get("ram_gb", 0.0)
    cpu_cores = hw.get("cpu_cores", 1.0)
    profile_name = hw.get("profile_name", "Auto")

    # Visual gauge meters
    ram_bar = mini_progress_bar(min(ram_mb, 8192), 8192, 12, GREEN)
    cpu_bar = mini_progress_bar(min(cpu_cores, 16.0), 16.0, 12, CYAN)

    out = []
    out.append(render_box_top("SYSTEM HARDWARE & ADAPTIVE PROFILE", f"{GREEN}● READY{RESET}", border_color))
    out.append(render_box_line(f"{YELLOW}RAM Capacity:{RESET}    [{ram_bar}] {WHITE}{ram_mb} MB ({ram_gb} GB){RESET} • {DIM}Container Safe{RESET}", border_color))
    out.append(render_box_line(f"{YELLOW}CPU Allocation:{RESET}  [{cpu_bar}] {WHITE}{cpu_cores} vCPU Cores{RESET} • {DIM}Real-Time Engine{RESET}", border_color))
    out.append(render_box_line(f"{YELLOW}Active Encoder:{RESET}  {CYAN}⚡ {WHITE}{encoder}{RESET} {GREEN}(H.264 Zero-Lag Auto-Detected){RESET}", border_color))
    out.append(render_box_line(f"{YELLOW}Recommended:{RESET}     {MAGENTA}💎 {WHITE}{profile_name}{RESET} {DIM}(Adaptive Auto-Tuned){RESET}", border_color))
    out.append(render_box_line(f"{YELLOW}Adaptive Guard:{RESET}  {CYAN}🛡️  Auto-Downgrade Active{RESET} {DIM}(Watchdog: < 0.85x){RESET}", border_color))
    out.append(render_box_line(f"{YELLOW}Diagnostic Logs:{RESET} {WHITE}📄 {CYAN}{log_path}{RESET} {DIM}(Continuous Realtime){RESET}", border_color))
    out.append(render_box_bottom(border_color))
    return "\n".join(out)
