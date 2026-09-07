"""
================================================================================
MagicStream Dynamic Broadcast Overlay Generator
Author: Shubham Kumar Jha
License: MIT
================================================================================
Generates broadcast-grade on-screen graphics on the fly:
1. Zee Music / MTV style "Now Playing" & "Up Next" lower-third cards (SVG).
2. CNN / BBC style "BREAKING NEWS" lower-third banners & scrolling tickers.
3. Over-The-Shoulder (OTS) news media window with real story photographs.

PNG pre-rendering uses Pillow (PIL) for reliable compositing — FFmpeg's librsvg
silently drops embedded base64 images, so we composite the photo directly.
"""

import base64
import os
import subprocess
import time
import xml.sax.saxutils as saxutils
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


def escape_xml(s: str) -> str:
    """Safely escapes text for SVG XML rendering."""
    return saxutils.escape(str(s or "").strip())


def _truncate_at_word(text: str, max_chars: int) -> str:
    """Truncates text at the last word boundary before max_chars."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Find the last space to break at a word boundary
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        return truncated[:last_space] + "..."
    return truncated + "..."


def _wrap_text(text: str, max_chars: int) -> List[str]:
    """Wraps text into lines at word boundaries."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if current_line and len(current_line) + 1 + len(word) > max_chars:
            lines.append(current_line)
            current_line = word
        else:
            current_line = f"{current_line} {word}" if current_line else word
    if current_line:
        lines.append(current_line)
    return lines


class OverlayGenerator:
    """Generates dynamic, real-time broadcast overlays for live streams."""

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
    def _render_news_overlay_png(
        headline: str,
        category: str,
        source: str,
        ticker_items: Optional[List[str]],
        image_path: Optional[str],
        topic: str,
        output_path: str,
    ) -> Optional[str]:
        """
        Renders the TV broadcast overlay as a transparent 1280x720 PNG using Pillow.
        This bypasses FFmpeg's librsvg which silently drops base64 images.
        Composites the real news story photograph directly via PIL.
        """
        W, H = 1280, 720
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Try to load a TrueType font, fall back to default
        try:
            font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
            font_xs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
            font_cat = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
            font_headline = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
            font_ticker = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
        except (OSError, IOError):
            font_lg = ImageFont.load_default()
            font_md = font_lg
            font_sm = font_lg
            font_xs = font_lg
            font_cat = font_lg
            font_headline = font_lg
            font_ticker = font_lg

        # Map publisher to authentic TV brand color
        src_upper = source.upper()
        if "BBC" in src_upper:
            source_bg = (187, 25, 25)
        elif "WASHINGTON POST" in src_upper:
            source_bg = (15, 23, 42)
        elif "REUTERS" in src_upper:
            source_bg = (234, 88, 12)
        elif "AL JAZEERA" in src_upper or "ALJAZEERA" in src_upper:
            source_bg = (194, 65, 12)
        elif "CNN" in src_upper:
            source_bg = (185, 28, 28)
        elif "FOX" in src_upper:
            source_bg = (30, 58, 138)
        elif "NDTV" in src_upper:
            source_bg = (153, 27, 27)
        elif "TIMES OF INDIA" in src_upper:
            source_bg = (180, 83, 9)
        else:
            source_bg = (3, 105, 161)

        # ═══════════════════════════════════════════════
        # TOP-RIGHT: OTS NEWS MEDIA WINDOW (510x310 @ 730,42)
        # ═══════════════════════════════════════════════
        ots_x, ots_y = 730, 42
        ots_w, ots_h = 510, 310

        # OTS glass panel background
        ots_panel = Image.new("RGBA", (ots_w, ots_h), (5, 10, 20, 240))
        ots_draw = ImageDraw.Draw(ots_panel)
        ots_draw.rounded_rectangle((0, 0, ots_w - 1, ots_h - 1), radius=14, outline=(0, 240, 255, 216), width=2)

        # Corner brackets
        for bx, by in [(12, 4), (ots_w - 12, 4), (12, ots_h - 6), (ots_w - 12, ots_h - 6)]:
            ots_draw.rectangle((bx - 4, by - 1, bx + 4, by + 1), fill=(0, 240, 255, 180))
            ots_draw.rectangle((bx - 1, by - 4, bx + 1, by + 4), fill=(0, 240, 255, 180))

        # Category ribbon (top-left angled)
        ots_draw.polygon([(0, 0), (260, 0), (235, 30), (0, 30)], fill=(220, 38, 38, 255))
        cat_text = f"🔴 {category.upper()[:22]}"
        ots_draw.text((34, 8), cat_text, fill=(255, 255, 255), font=font_cat)

        # Satellite relay badge (top-right)
        ots_draw.rounded_rectangle((360, 6, 500, 26), radius=4, fill=(3, 105, 161, 216))
        ots_draw.text((370, 9), "📡 LIVE VIDEO RELAY", fill=(255, 255, 255), font=font_xs)

        # ── LEFT SIDE: STORY PHOTOGRAPH ──
        photo_x, photo_y, photo_w, photo_h = 20, 38, 230, 130
        photo_loaded = False

        if image_path and os.path.exists(image_path):
            try:
                story_photo = Image.open(image_path).convert("RGB")
                story_photo = ImageOps.fit(story_photo, (photo_w, photo_h), method=Image.Resampling.LANCZOS)

                # Rounded corner mask for the photo
                photo_mask = Image.new("L", (photo_w, photo_h), 0)
                ImageDraw.Draw(photo_mask).rounded_rectangle((0, 0, photo_w, photo_h), radius=8, fill=255)

                # Paste photo with rounded corners onto OTS panel
                photo_rgba = story_photo.copy().convert("RGBA")
                photo_rgba.putalpha(photo_mask)
                ots_panel.paste(story_photo, (photo_x, photo_y), photo_mask)

                # Cyan border around photo
                ots_draw.rounded_rectangle(
                    (photo_x, photo_y, photo_x + photo_w, photo_y + photo_h),
                    radius=8, outline=(0, 240, 255, 200), width=2
                )

                # "LIVE PHOTO" badge
                ots_draw.rounded_rectangle((photo_x + 6, photo_y + 6, photo_x + 100, photo_y + 24), radius=3, fill=(239, 68, 68, 230))
                ots_draw.ellipse((photo_x + 10, photo_y + 11, photo_x + 16, photo_y + 17), fill=(255, 255, 255))
                ots_draw.text((photo_x + 20, photo_y + 8), "LIVE PHOTO", fill=(255, 255, 255), font=font_xs)
                photo_loaded = True
            except Exception:
                photo_loaded = False

        if not photo_loaded:
            # Fallback: dark satellite radar panel
            ots_draw.rounded_rectangle(
                (photo_x, photo_y, photo_x + photo_w, photo_y + photo_h),
                radius=8, fill=(10, 20, 36, 230), outline=(0, 240, 255, 150), width=2
            )
            ots_draw.text((photo_x + 60, photo_y + 50), "🌐", fill=(56, 189, 248), font=font_lg)
            ots_draw.text((photo_x + 40, photo_y + 90), "SATELLITE WIRE", fill=(56, 189, 248), font=font_sm)

        # ── RIGHT SIDE: PUBLISHER BADGE & TELEMETRY ──
        pb_x, pb_y, pb_w, pb_h = 260, 38, 230, 34
        ots_draw.rounded_rectangle((pb_x, pb_y, pb_x + pb_w, pb_y + pb_h), radius=6, fill=source_bg + (255,), outline=(51, 65, 85, 200))
        ots_draw.text((pb_x + 12, pb_y + 8), f"⚡ {source.upper()[:20]}", fill=(255, 255, 255), font=font_md)

        # Telemetry intel box
        tel_x, tel_y, tel_w, tel_h = 260, 78, 230, 90
        ots_draw.rounded_rectangle((tel_x, tel_y, tel_x + tel_w, tel_y + tel_h), radius=6, fill=(10, 20, 36, 230), outline=(30, 41, 59, 200))
        ots_draw.ellipse((tel_x + 10, tel_y + 14, tel_x + 17, tel_y + 21), fill=(56, 189, 248))
        ots_draw.text((tel_x + 24, tel_y + 12), "1080p Satellite Feed", fill=(56, 189, 248), font=font_sm)
        ots_draw.ellipse((tel_x + 10, tel_y + 38, tel_x + 17, tel_y + 45), fill=(34, 197, 94))
        ots_draw.text((tel_x + 24, tel_y + 36), "● VERIFIED BROADCAST", fill=(34, 197, 94), font=font_sm)
        ots_draw.ellipse((tel_x + 10, tel_y + 62, tel_x + 17, tel_y + 69), fill=(251, 191, 36))
        ots_draw.text((tel_x + 24, tel_y + 60), f"TOPIC: {topic.upper()[:18]}", fill=(203, 213, 225), font=font_sm)

        # Divider
        ots_draw.line([(20, 178), (490, 178)], fill=(51, 65, 85, 200), width=1)

        # Headline in OTS — word-wrapped to 2 lines
        hl_lines = _wrap_text(headline, 42)
        y_offset = 190
        for line in hl_lines[:2]:
            ots_draw.text((20, y_offset), line, fill=(255, 255, 255), font=font_md)
            y_offset += 20

        # Source attribution bar at bottom
        ots_draw.rectangle((0, 235, ots_w, ots_h), fill=(6, 12, 22, 245))
        # Gold accent line
        for gx in range(ots_w):
            frac = gx / max(ots_w, 1)
            r = int(217 + (251 - 217) * frac)
            g = int(119 + (191 - 119) * frac)
            b = int(6 + (36 - 6) * frac)
            ots_draw.point((gx, 233), fill=(r, g, b, 255))
            ots_draw.point((gx, 234), fill=(r, g, b, 255))

        ots_draw.text((20, 244), f"⚡ SOURCE: {source.upper()}", fill=(251, 191, 36), font=font_sm)
        ots_draw.text((20, 262), "⚖️ FAIR USE / EDITORIAL • CC-BY 4.0", fill=(100, 116, 139), font=font_xs)
        ots_draw.text((20, 278), "(SEC 107 U.S. & SEC 52(1)(a) INDIAN COPYRIGHT ACT)", fill=(71, 85, 105), font=font_xs)

        # Paste OTS panel onto main canvas
        img.paste(ots_panel, (ots_x, ots_y), ots_panel)

        # ═══════════════════════════════════════════════
        # BOTTOM: LOWER-THIRD & TICKER (at y=525)
        # ═══════════════════════════════════════════════
        lt_x, lt_y = 20, 525
        lt_w = 1240

        # Breaking News angled trapezoid
        draw.polygon([(lt_x, lt_y), (lt_x + 320, lt_y), (lt_x + 290, lt_y + 42), (lt_x, lt_y + 42)],
                      fill=(220, 38, 38, 250))
        # Gold border
        draw.line([(lt_x, lt_y + 42), (lt_x + 290, lt_y + 42)], fill=(251, 191, 36, 200), width=2)
        draw.text((lt_x + 32, lt_y + 10), "⚡ BREAKING NEWS", fill=(255, 255, 255), font=font_md)

        # Location & Clock badge
        time_str = time.strftime("%H:%M") + " IST"
        draw.polygon([(lt_x + 295, lt_y), (lt_x + 560, lt_y), (lt_x + 535, lt_y + 42), (lt_x + 270, lt_y + 42)],
                      fill=(15, 23, 42, 240))
        draw.ellipse((lt_x + 310, lt_y + 16, lt_x + 320, lt_y + 26), fill=(239, 68, 68))
        draw.text((lt_x + 330, lt_y + 12), f"LIVE • NEW DELHI • {time_str}", fill=(255, 255, 255), font=font_sm)

        # Source ribbon (right edge)
        draw.polygon([(lt_x + 1010, lt_y + 10), (lt_x + lt_w, lt_y + 10), (lt_x + lt_w, lt_y + 42), (lt_x + 985, lt_y + 42)],
                      fill=(30, 41, 59, 240))
        draw.text((lt_x + 1020, lt_y + 18), f"FEED: {source.upper()[:18]}", fill=(56, 189, 248), font=font_sm)

        # Main headline plate
        draw.rectangle((lt_x, lt_y + 42, lt_x + lt_w, lt_y + 134), fill=(7, 13, 24, 248))
        draw.rectangle((lt_x, lt_y + 42, lt_x + lt_w, lt_y + 134), outline=(30, 41, 59, 200), width=2)
        # Red accent strip on left
        draw.rectangle((lt_x, lt_y + 42, lt_x + 8, lt_y + 134), fill=(220, 38, 38, 250))

        # Main headline text — word-wrapped to 2 lines
        hl_wrapped = _wrap_text(headline, 65)
        hl_y = lt_y + 65
        for hl_line in hl_wrapped[:2]:
            draw.text((lt_x + 30, hl_y), hl_line, fill=(255, 255, 255), font=font_headline)
            hl_y += 32

        # Running ticker strip
        draw.rectangle((lt_x, lt_y + 134, lt_x + lt_w, lt_y + 176), fill=(5, 9, 18, 245))
        draw.rectangle((lt_x, lt_y + 134, lt_x + lt_w, lt_y + 176), outline=(0, 240, 255, 100), width=1)

        # Yellow "TOP STORIES" tag
        draw.rectangle((lt_x, lt_y + 134, lt_x + 165, lt_y + 176), fill=(234, 179, 8, 255))
        draw.text((lt_x + 20, lt_y + 148), "▶ TOP STORIES", fill=(0, 0, 0), font=font_ticker)

        # Ticker headlines
        if ticker_items:
            ticker_text = "   ✦   ".join(t[:60] for t in ticker_items[:5])
        else:
            ticker_text = "24/7 Global Satellite Live Feed   ✦   Verified Real-Time Broadcast Wire"
        draw.text((lt_x + 185, lt_y + 148), ticker_text[:130], fill=(248, 250, 252), font=font_ticker)

        # Save as transparent PNG
        try:
            img.save(output_path, "PNG")
            return output_path
        except Exception:
            return None

    @staticmethod
    def generate_news_lower_third(
        headline: str,
        category: str = "BREAKING NEWS",
        source: str = "Live Wire",
        ticker_items: Optional[List[str]] = None,
        image_path: Optional[str] = None,
        topic: str = "breaking",
        output_path: str = "overlay/breaking_news.svg"
    ) -> str:
        """
        Generates an authentic TV broadcast graphics layer (1280x720):
        - Top-Right: Over-The-Shoulder (OTS) News Media Window with real story photograph & verified publisher
        - Bottom: Multi-tier 3D angled Breaking News lower-third with clock, city bug, and live ticker
        - Left: Open broadcast window for the AI Anchorwoman

        Also pre-renders a reliable PNG overlay using Pillow (not FFmpeg librsvg).
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        safe_headline = escape_xml(headline or "Top Story Updating Live...")
        if len(safe_headline) > 75:
            safe_headline = _truncate_at_word(safe_headline, 72)

        safe_cat = escape_xml(category.upper() if category else "BREAKING NEWS")
        safe_source = escape_xml(source.upper() if source else "GLOBAL WIRE")
        safe_topic = escape_xml(topic.upper() if topic else "BREAKING")

        # Encode news photo to base64 for the SVG (used as fallback)
        b64_photo = ""
        resolved_img = image_path if image_path and os.path.exists(image_path) else "overlay/current_story_photo.jpg"
        if resolved_img and os.path.exists(resolved_img):
            try:
                with open(resolved_img, "rb") as f_img:
                    b64_photo = base64.b64encode(f_img.read()).decode("ascii")
            except Exception:
                b64_photo = ""

        # Map publisher to authentic TV brand color
        src_upper = safe_source.upper()
        if "BBC" in src_upper:
            source_bg = "#bb1919"
        elif "WASHINGTON POST" in src_upper:
            source_bg = "#0f172a"
        elif "REUTERS" in src_upper:
            source_bg = "#ea580c"
        elif "AL JAZEERA" in src_upper:
            source_bg = "#c2410c"
        elif "CNN" in src_upper:
            source_bg = "#b91c1c"
        elif "FOX" in src_upper:
            source_bg = "#1e3a8a"
        elif "NDTV" in src_upper:
            source_bg = "#991b1b"
        elif "TIMES OF INDIA" in src_upper:
            source_bg = "#b45309"
        else:
            source_bg = "#0369a1"

        if ticker_items:
            safe_ticker = "   ✦   ".join(escape_xml(t) for t in ticker_items[:5])
        else:
            safe_ticker = "24/7 Global Satellite Live Feed   ✦   Verified Real-Time Broadcast Wire   ✦   Breaking Alerts Continuous"

        if len(safe_ticker) > 140:
            safe_ticker = safe_ticker[:137] + "..."

        # Live clock time string e.g. "16:20 IST"
        time_str = time.strftime("%H:%M") + " IST"

        # Construct photo SVG block or fallback radar
        if b64_photo:
            photo_block = f"""
    <!-- REAL NEWS STORY PHOTOGRAPH -->
    <image href="data:image/jpeg;base64,{b64_photo}" x="20" y="38" width="230" height="130" preserveAspectRatio="xMidYMid slice" clip-path="url(#otsPhotoClip)"/>
    <rect x="20" y="38" width="230" height="130" rx="8" fill="none" stroke="#00f0ff" stroke-width="1.8"/>
    <!-- Top-Left Badge on Photo -->
    <rect x="26" y="44" width="94" height="18" rx="3" fill="#ef4444"/>
    <circle cx="34" cy="53" r="3" fill="#ffffff"/>
    <text x="74" y="56" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="9" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="0.5">LIVE PHOTO</text>
"""
        else:
            photo_block = f"""
    <!-- FALLBACK SATELLITE WIRE RADAR -->
    <rect x="20" y="38" width="230" height="130" rx="8" fill="#0a1424" stroke="#00f0ff" stroke-width="1.5"/>
    <circle cx="135" cy="103" r="42" fill="none" stroke="#00f0ff" stroke-width="1" stroke-dasharray="3,3" opacity="0.4"/>
    <circle cx="135" cy="103" r="24" fill="none" stroke="#38bdf8" stroke-width="1.2" opacity="0.6"/>
    <text x="135" y="108" font-size="20" text-anchor="middle" fill="#38bdf8">🌐</text>
    <text x="135" y="152" font-family="'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="800" fill="#38bdf8" text-anchor="middle">SATELLITE INTEL WIRE</text>
"""

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <!-- Photo Clip Path -->
    <clipPath id="otsPhotoClip">
      <rect x="20" y="38" width="230" height="130" rx="8" ry="8"/>
    </clipPath>

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

    <!-- Top Tab: Category Ribbon -->
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

    <!-- LEFT: REAL STORY PHOTOGRAPH / MEDIA FRAME -->
    {photo_block}

    <!-- RIGHT: VERIFIED PUBLISHER BRANDING & TELEMETRY -->
    <rect x="260" y="38" width="230" height="34" rx="6" fill="{source_bg}" stroke="#334155" stroke-width="1"/>
    <text x="272" y="60" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="12" font-weight="900" fill="#ffffff" letter-spacing="0.5">
      ⚡ {safe_source[:20]}
    </text>

    <!-- Telemetry Intel Box -->
    <rect x="260" y="78" width="230" height="90" rx="6" fill="#0a1424" stroke="#1e293b" stroke-width="1"/>
    <circle cx="274" cy="98" r="3.5" fill="#38bdf8"/>
    <text x="286" y="102" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="10" font-weight="700" fill="#38bdf8">
      1080p Satellite Feed
    </text>
    <circle cx="274" cy="122" r="3.5" fill="#22c55e"/>
    <text x="286" y="126" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="10" font-weight="800" fill="#22c55e">
      ● VERIFIED BROADCAST WIRE
    </text>
    <circle cx="274" cy="146" r="3.5" fill="#fbbf24"/>
    <text x="286" y="150" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="10" font-weight="800" fill="#cbd5e1">
      TOPIC: {safe_topic[:18]}
    </text>

    <!-- Divider Line -->
    <line x1="20" y1="178" x2="490" y2="178" stroke="#334155" stroke-width="1.2"/>

    <!-- Headline Summary Text in OTS Frame -->
    <text x="20" y="200" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="14" font-weight="800" fill="#ffffff">
      {safe_headline[:58]}
    </text>
    <text x="20" y="218" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="12" font-weight="600" fill="#94a3b8">
      Continuous 24/7 Coverage Across All Global Telemetry Points
    </text>

    <!-- Source Attribution Bottom Bar with CC Legal Notice -->
    <rect x="0" y="235" width="510" height="75" rx="0" ry="0" fill="#060c16"/>
    <rect x="0" y="233" width="510" height="2" fill="url(#goldAccent)"/>
    
    <!-- Source Row -->
    <text x="20" y="258" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="11" font-weight="900" fill="#fbbf24" letter-spacing="1">
      ⚡ SOURCE: <tspan fill="#38bdf8" font-weight="800">{safe_source}</tspan>
    </text>

    <!-- Creative Commons & Legal Protection Notice -->
    <text x="20" y="278" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="9" font-weight="700" fill="#64748b" letter-spacing="0.4">
      ⚖️ FAIR USE / EDITORIAL NEWS REPORTING • CC-BY 4.0
    </text>
    <text x="20" y="294" font-family="'Segoe UI', Roboto, Helvetica, sans-serif" font-size="8.5" font-weight="700" fill="#475569" letter-spacing="0.4">
      (SEC 107 U.S. COPYRIGHT ACT &amp; SEC 52(1)(a) INDIAN COPYRIGHT ACT)
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

        # ── Pre-render to reliable PNG using Pillow ──
        # FFmpeg's librsvg silently drops base64 images, so we use Pillow
        # which composites the story photo directly and guarantees it appears.
        if output_path.endswith(".svg"):
            png_path = output_path[:-4] + ".png"
            OverlayGenerator._render_news_overlay_png(
                headline=headline or "Top Story Updating Live...",
                category=category,
                source=source,
                ticker_items=ticker_items,
                image_path=image_path,
                topic=topic,
                output_path=png_path,
            )

        return output_path
