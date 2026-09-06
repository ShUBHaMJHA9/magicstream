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
        Generates a CNN / BBC / Zee News style dynamic Breaking News lower-third banner.
        Dimensions: 1280x180 px.
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        safe_headline = escape_xml(headline or "Top Story Updating Live...")
        if len(safe_headline) > 65:
            safe_headline = safe_headline[:62] + "..."

        safe_cat = escape_xml(category or "BREAKING NEWS")
        safe_source = escape_xml(source or "Reuters / AP")

        if ticker_items:
            safe_ticker = "   •   ".join(escape_xml(t) for t in ticker_items[:4])
        else:
            safe_ticker = "24/7 Global Live Feed   •   Verified Live Coverage   •   Real-time Wire"

        if len(safe_ticker) > 110:
            safe_ticker = safe_ticker[:107] + "..."

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="180" viewBox="0 0 1280 180">
  <defs>
    <linearGradient id="redBadge" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#b91c1c"/>
      <stop offset="100%" stop-color="#dc2626"/>
    </linearGradient>
    <linearGradient id="headlineBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#111827" stop-opacity="0.92"/>
    </linearGradient>
    <linearGradient id="tickerBg" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#fbbf24"/>
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.7"/>
    </filter>
  </defs>

  <!-- Main Headline Box -->
  <rect x="20" y="36" width="1240" height="88" rx="10" ry="10" fill="url(#headlineBg)" stroke="#334155" stroke-width="1.5" filter="url(#shadow)"/>

  <!-- Top Red BREAKING NEWS Badge -->
  <path d="M 20 6 L 270 6 L 250 38 L 20 38 Z" fill="url(#redBadge)"/>
  <circle cx="42" cy="22" r="5" fill="#ffffff"/>
  <text x="56" y="27" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="15" font-weight="900" fill="#ffffff" letter-spacing="1.5">
    {safe_cat}
  </text>

  <!-- Source Badge (Right) -->
  <rect x="1080" y="46" width="160" height="24" rx="6" ry="6" fill="#1e293b"/>
  <text x="1160" y="63" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="700" fill="#38bdf8" text-anchor="middle">
    SOURCE: {safe_source}
  </text>

  <!-- Headline Text -->
  <text x="44" y="92" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="24" font-weight="800" fill="#ffffff">
    {safe_headline}
  </text>

  <!-- Bottom Ticker Bar -->
  <rect x="20" y="128" width="1240" height="38" rx="6" ry="6" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
  <rect x="20" y="128" width="110" height="38" rx="6" ry="6" fill="url(#tickerBg)"/>
  <text x="75" y="152" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="12" font-weight="900" fill="#000000" text-anchor="middle" letter-spacing="1">
    UPDATES
  </text>
  <text x="145" y="152" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="13" font-weight="600" fill="#f1f5f9">
    {safe_ticker}
  </text>
</svg>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg)

        return output_path
