"""
================================================================================
MagicStream Dynamic Broadcast Overlay Generator
Author: Shubham Kumar Jha
License: MIT
================================================================================
Generates broadcast-grade on-screen SVG graphics on the fly:
1. Zee Music / MTV style "Now Playing" & "Up Next" lower-third cards.
2. CNN / BBC style "BREAKING NEWS" lower-third banners & scrolling tickers.
"""

import os
import time
import xml.sax.saxutils as saxutils
from typing import List, Optional


def escape_xml(s: str) -> str:
    """Safely escapes text for SVG XML rendering."""
    return saxutils.escape(str(s or "").strip())


class OverlayGenerator:
    """Generates dynamic, real-time SVG broadcast overlays for live streams."""

    @staticmethod
    def generate_music_card(
        current_title: str,
        next_title: str = "",
        output_path: str = "overlay/now_playing.svg",
        channel_name: str = "MAGICSTREAM LIVE",
        style: str = "cyberpunk"
    ) -> str:
        """
        Generates a sleek, Zee Music / MTV style glassmorphic lower-third music card.
        Dimensions: 820x150 px.
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        safe_curr = escape_xml(current_title or "Live Audio Stream")
        if len(safe_curr) > 42:
            safe_curr = safe_curr[:39] + "..."

        safe_next = escape_xml(next_title or "Sequential Playlist Loop")
        if len(safe_next) > 45:
            safe_next = safe_next[:42] + "..."

        safe_channel = escape_xml(channel_name)

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="820" height="150" viewBox="0 0 820 150">
  <defs>
    <linearGradient id="cardBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#080c16" stop-opacity="0.94"/>
      <stop offset="100%" stop-color="#141c2f" stop-opacity="0.90"/>
    </linearGradient>
    <linearGradient id="neonGlow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00f0ff"/>
      <stop offset="50%" stop-color="#a855f7"/>
      <stop offset="100%" stop-color="#ec4899"/>
    </linearGradient>
    <filter id="dropShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#000" flood-opacity="0.65"/>
    </filter>
  </defs>

  <!-- Main Glassmorphic Card Container -->
  <rect x="6" y="6" width="808" height="138" rx="18" ry="18" fill="url(#cardBg)" stroke="url(#neonGlow)" stroke-width="2.5" filter="url(#dropShadow)"/>

  <!-- Left Accent Color Bar -->
  <rect x="6" y="6" width="10" height="138" rx="5" ry="5" fill="url(#neonGlow)"/>

  <!-- Live Equalizer / Music Icon Badge -->
  <g transform="translate(30, 24)">
    <rect x="0" y="8" width="5" height="18" rx="2" fill="#00f0ff"/>
    <rect x="9" y="0" width="5" height="26" rx="2" fill="#a855f7"/>
    <rect x="18" y="12" width="5" height="14" rx="2" fill="#ec4899"/>
    <rect x="27" y="4" width="5" height="22" rx="2" fill="#00f0ff"/>
  </g>

  <!-- Channel Header Badge -->
  <text x="74" y="42" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="13" font-weight="800" fill="#00f0ff" letter-spacing="2">
    ● LIVE <tspan fill="#94a3b8">| {safe_channel}</tspan>
  </text>

  <!-- NOW PLAYING Row -->
  <text x="30" y="78" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="15" font-weight="900" fill="#facc15" letter-spacing="1">
    NOW PLAYING:
  </text>
  <text x="160" y="78" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="19" font-weight="700" fill="#ffffff">
    {safe_curr}
  </text>

  <!-- UP NEXT Row -->
  <g opacity="0.92">
    <text x="30" y="118" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="13" font-weight="700" fill="#38bdf8" letter-spacing="0.5">
      UP NEXT:
    </text>
    <text x="108" y="118" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="15" font-weight="600" fill="#cbd5e1">
      {safe_next}
    </text>
  </g>

  <!-- Right Music Note Icon -->
  <text x="765" y="52" font-size="28" fill="#a855f7" opacity="0.75">🎵</text>
</svg>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)

        return output_path

    @staticmethod
    def generate_news_lower_third(
        headline: str,
        category: str = "BREAKING NEWS",
        source: str = "Live Wire",
        ticker_items: Optional[List[str]] = None,
        output_path: str = "overlay/breaking_news.svg"
    ) -> str:
        """
        Generates an authentic TV broadcast graphics layer (1280x720):
        - Top-Right: Over-The-Shoulder (OTS) News Media Window with source badge & topic graphic
        - Bottom: Multi-tier 3D angled Breaking News lower-third with clock, city bug, and live ticker
        - Left: Open broadcast window for the AI Anchorwoman
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        safe_headline = escape_xml(headline or "Top Story Updating Live...")
        if len(safe_headline) > 75:
            safe_headline = safe_headline[:72] + "..."

        safe_cat = escape_xml(category.upper() if category else "BREAKING NEWS")
        safe_source = escape_xml(source.upper() if source else "GLOBAL WIRE")

        # Format 2-line wrapped text for the OTS media window
        ots_words = safe_headline.split(" ")
        ots_line1 = " ".join(ots_words[:6])
        ots_line2 = " ".join(ots_words[6:12])
        if len(ots_words) > 12:
            ots_line2 += "..."

        if ticker_items:
            safe_ticker = "   ✦   ".join(escape_xml(t) for t in ticker_items[:5])
        else:
            safe_ticker = "24/7 Global Satellite Live Feed   ✦   Verified Real-Time Broadcast Wire   ✦   Breaking Alerts Continuous"

        if len(safe_ticker) > 140:
            safe_ticker = safe_ticker[:137] + "..."

        # Live clock time string e.g. "16:20 IST"
        time_str = time.strftime("%H:%M") + " IST"

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <!-- Gradients -->
    <linearGradient id="breakingRed" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#991b1b"/>
      <stop offset="40%" stop-color="#dc2626"/>
      <stop offset="100%" stop-color="#b91c1c"/>
    </linearGradient>
    <linearGradient id="goldAccent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#d97706"/>
      <stop offset="50%" stop-color="#fbbf24"/>
      <stop offset="100%" stop-color="#f59e0b"/>
    </linearGradient>
    <linearGradient id="otsBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#050a14" stop-opacity="0.94"/>
      <stop offset="100%" stop-color="#0c192c" stop-opacity="0.90"/>
    </linearGradient>
    <linearGradient id="headlineBg" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#070d18" stop-opacity="0.98"/>
      <stop offset="85%" stop-color="#0f172a" stop-opacity="0.96"/>
      <stop offset="100%" stop-color="#1e293b" stop-opacity="0.90"/>
    </linearGradient>
    <linearGradient id="tickerYellow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#eab308"/>
      <stop offset="100%" stop-color="#facc15"/>
    </linearGradient>

    <!-- Filters -->
    <filter id="glowRed" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="#ef4444" flood-opacity="0.75"/>
    </filter>
    <filter id="panelShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#000000" flood-opacity="0.85"/>
    </filter>
  </defs>

  <!-- ====================================================================== -->
  <!-- TOP-RIGHT: OVER-THE-SHOULDER (OTS) NEWS MEDIA & SOURCE WINDOW          -->
  <!-- ====================================================================== -->
  <g id="ots_news_window" transform="translate(730, 42)" filter="url(#panelShadow)">
    <!-- Outer Glass Panel with Angled Corners -->
    <rect x="0" y="0" width="510" height="310" rx="14" ry="14" fill="url(#otsBg)" stroke="#00f0ff" stroke-width="1.8" stroke-opacity="0.85"/>

    <!-- Corner Decorative Brackets -->
    <path d="M 12 4 L 4 4 L 4 12" stroke="#00f0ff" stroke-width="3" fill="none"/>
    <path d="M 498 4 L 506 4 L 506 12" stroke="#00f0ff" stroke-width="3" fill="none"/>
    <path d="M 12 306 L 4 306 L 4 298" stroke="#00f0ff" stroke-width="3" fill="none"/>
    <path d="M 498 306 L 506 306 L 506 298" stroke="#00f0ff" stroke-width="3" fill="none"/>

    <!-- Top Tab: Category & Satellite Telemetry -->
    <path d="M 0 0 L 260 0 L 235 30 L 0 30 Z" fill="url(#breakingRed)"/>
    <circle cx="20" cy="15" r="4.5" fill="#ffffff" filter="url(#glowRed)"/>
    <text x="34" y="20" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="11" font-weight="900" fill="#ffffff" letter-spacing="1.5">
      🔴 {safe_cat}
    </text>

    <!-- Satellite Video Relay Badge (Top Right) -->
    <rect x="360" y="6" width="140" height="20" rx="4" fill="#0369a1" opacity="0.85"/>
    <text x="430" y="19" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="9" font-weight="800" fill="#ffffff" text-anchor="middle" letter-spacing="0.5">
      📡 LIVE VIDEO RELAY
    </text>

    <!-- MULTI-IMAGE / TELEMETRY GRID -->
    <!-- Grid Box 1: Visual Radar / Global Wire -->
    <rect x="20" y="38" width="220" height="92" rx="8" fill="#0a1424" stroke="#1e293b" stroke-width="1"/>
    <circle cx="50" cy="84" r="28" fill="none" stroke="#00f0ff" stroke-width="1" stroke-dasharray="3,3" opacity="0.4"/>
    <circle cx="50" cy="84" r="16" fill="none" stroke="#38bdf8" stroke-width="1.2" opacity="0.6"/>
    <text x="50" y="90" font-size="16" text-anchor="middle" fill="#38bdf8">🌐</text>
    <text x="88" y="70" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="11" font-weight="800" fill="#38bdf8">
      GLOBAL WIRE
    </text>
    <text x="88" y="86" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="9" font-weight="600" fill="#94a3b8">
      1080p Satellite Feed
    </text>
    <text x="88" y="100" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="9" font-weight="700" fill="#22c55e">
      ● ENCRYPTED LIVE
    </text>

    <!-- Grid Box 2: Editorial Topic Intel -->
    <rect x="250" y="38" width="240" height="92" rx="8" fill="#0a1424" stroke="#1e293b" stroke-width="1"/>
    <rect x="260" y="48" width="70" height="18" rx="4" fill="#991b1b"/>
    <text x="295" y="61" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="9" font-weight="900" fill="#ffffff" text-anchor="middle">
      HOT TOPIC
    </text>
    <text x="260" y="82" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="12" font-weight="800" fill="#ffffff">
      {ots_line1}
    </text>
    <text x="260" y="98" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="10" font-weight="600" fill="#cbd5e1">
      {ots_line2}
    </text>

    <!-- Headline Summary Text -->
    <text x="20" y="152" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="16" font-weight="800" fill="#ffffff">
      {safe_headline}
    </text>

    <!-- Divider Line -->
    <line x1="20" y1="172" x2="490" y2="172" stroke="#334155" stroke-width="1.2"/>

    <!-- Verified News Wire Key Intel Bullets -->
    <g transform="translate(20, 192)">
      <circle cx="6" cy="-4" r="3" fill="#fbbf24"/>
      <text x="18" y="0" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="11" font-weight="700" fill="#e2e8f0">
        Live Broadcast Wire: {safe_source}
      </text>

      <circle cx="6" cy="18" r="3" fill="#00f0ff"/>
      <text x="18" y="22" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="11" font-weight="700" fill="#e2e8f0">
        Round-the-Clock AI Studio Verification
      </text>

      <circle cx="6" cy="40" r="3" fill="#22c55e"/>
      <text x="18" y="44" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="11" font-weight="700" fill="#cbd5e1">
        High-Definition Multi-Platform Streaming Feed
      </text>
    </g>

    <!-- Source Attribution Bottom Bar with CC Legal Notice -->
    <rect x="0" y="255" width="510" height="55" rx="0" ry="0" fill="#060c16"/>
    <rect x="0" y="253" width="510" height="2" fill="url(#goldAccent)"/>
    
    <!-- Source Row -->
    <text x="20" y="275" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="11" font-weight="900" fill="#fbbf24" letter-spacing="1">
      ⚡ SOURCE:
    </text>
    <text x="85" y="275" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="12" font-weight="800" fill="#38bdf8">
      {safe_source}
    </text>

    <!-- Creative Commons & Legal Protection Notice -->
    <text x="20" y="296" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="9" font-weight="700" fill="#64748b" letter-spacing="0.4">
      ⚖️ FAIR USE / EDITORIAL NEWS REPORTING • CC-BY 4.0 (SEC 107 U.S. &amp; SEC 52(1)(a) INDIAN COPYRIGHT ACT)
    </text>
  </g>

  <!-- ====================================================================== -->
  <!-- BOTTOM: MULTI-TIER TV NEWS LOWER-THIRD & RUNNING TICKER               -->
  <!-- ====================================================================== -->
  <g id="tv_lower_third" transform="translate(20, 525)" filter="url(#panelShadow)">
    <!-- Top Bar: Angled BREAKING NEWS Badge & Location Clock -->
    <!-- Breaking News Angled Trapezoid -->
    <path d="M 0 0 L 320 0 L 290 42 L 0 42 Z" fill="url(#breakingRed)" stroke="#fbbf24" stroke-width="1.5"/>
    <text x="32" y="28" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="19" font-weight="900" fill="#ffffff" letter-spacing="2">
      ⚡ BREAKING NEWS
    </text>

    <!-- Location & Clock Badge -->
    <path d="M 295 0 L 560 0 L 535 42 L 270 42 Z" fill="#0f172a" stroke="#334155" stroke-width="1"/>
    <circle cx="315" cy="21" r="5" fill="#ef4444" filter="url(#glowRed)"/>
    <text x="330" y="26" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="13" font-weight="800" fill="#ffffff" letter-spacing="1">
      LIVE <tspan fill="#94a3b8">• NEW DELHI • {time_str}</tspan>
    </text>

    <!-- Secondary Category Ribbon (Right Edge) -->
    <path d="M 1030 10 L 1240 10 L 1240 42 L 1005 42 Z" fill="#1e293b"/>
    <text x="1220" y="30" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="12" font-weight="800" fill="#38bdf8" text-anchor="end" letter-spacing="1">
      FEED: {safe_source}
    </text>

    <!-- Main Headline Plate (Full Width) -->
    <rect x="0" y="42" width="1240" height="92" fill="url(#headlineBg)" stroke="#1e293b" stroke-width="1.5"/>
    <!-- Red Accent Left Strip -->
    <rect x="0" y="42" width="8" height="92" fill="url(#breakingRed)"/>

    <!-- Main Headline Text -->
    <text x="30" y="100" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="28" font-weight="900" fill="#ffffff" letter-spacing="0.5">
      {safe_headline}
    </text>

    <!-- Running Ticker Strip (Bottom Tier) -->
    <rect x="0" y="134" width="1240" height="42" fill="#050912" stroke="#00f0ff" stroke-width="0.8"/>
    <!-- Yellow TOP STORIES Tag -->
    <rect x="0" y="134" width="165" height="42" fill="url(#tickerYellow)"/>
    <text x="82" y="161" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="13" font-weight="900" fill="#000000" text-anchor="middle" letter-spacing="1">
      ▶ TOP STORIES
    </text>

    <!-- Running Ticker Headlines -->
    <text x="185" y="161" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="14" font-weight="700" fill="#f8fafc">
      {safe_ticker}
    </text>
  </g>
</svg>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)

        return output_path

