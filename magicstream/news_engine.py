"""
================================================================================
MagicStream 24/7 Live Breaking News Broadcast Engine
Author: Shubham Kumar Jha
License: MIT
================================================================================
Automated live news channel studio:
1. Free, open-source RSS feed fetcher (Google News, BBC, Reuters, Tech) with zero API keys.
2. Breaking News lower-third overlay and scrolling ticker generator.
3. Automated AI speech anchor (TTS) and background news bed synthesizer.
"""

import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from magicstream.overlay_generator import OverlayGenerator

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False


# Predefined high-reliability public news RSS endpoints (zero API key required)
NEWS_FEEDS: Dict[str, str] = {
    "world": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "india": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "technology": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    "business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",
}


@dataclass
class NewsStory:
    title: str
    source: str
    category: str = "BREAKING NEWS"
    published: str = ""
    image_url: str = ""
    topic: str = "breaking"
    clean_headline: str = ""

    def __post_init__(self):
        # Strip trailing " - Publisher Name" often added by Google News RSS
        clean = self.title
        if " - " in clean:
            parts = clean.rsplit(" - ", 1)
            clean = parts[0].strip()
            if not self.source or self.source == "Google News":
                self.source = parts[1].strip()
        self.clean_headline = clean

        # Infer topic for visual telemetry plate
        c_low = (clean + " " + self.category).lower()
        if any(w in c_low for w in ["military", "war", "army", "navy", "tanker", "missile", "strike", "ship", "troops", "drone", "weapon"]):
            self.topic = "military"
        elif any(w in c_low for w in ["putin", "trump", "biden", "zelensky", "talks", "peace", "summit", "envoy", "diplomacy", "treaty"]):
            self.topic = "diplomacy"
        elif any(w in c_low for w in ["court", "trial", "judge", "election", "vote", "congress", "senate", "parliament", "gop", "democrat"]):
            self.topic = "politics"
        elif any(w in c_low for w in ["ai", "tech", "apple", "google", "meta", "nvidia", "cyber", "chip", "software", "robot"]):
            self.topic = "technology"
        elif any(w in c_low for w in ["market", "bank", "inflation", "economy", "trade", "dollar", "stock", "fed", "tariff", "rate"]):
            self.topic = "economy"
        elif any(w in c_low for w in ["india", "delhi", "mumbai", "modi", "bjp"]):
            self.topic = "india"
        else:
            self.topic = "breaking"


class NewsFetcher:
    """Fetches real-time breaking news stories from open public RSS feeds."""

    def __init__(self, default_category: str = "world"):
        self.category = default_category
        self.cached_stories: List[NewsStory] = []
        self.last_fetch_time: float = 0.0

    def fetch_stories(self, category: Optional[str] = None, limit: int = 15) -> List[NewsStory]:
        """Fetches top breaking news stories with graceful fallback."""
        cat = category or self.category
        feed_url = NEWS_FEEDS.get(cat.lower(), NEWS_FEEDS["world"])

        now = time.time()
        # Cache for 2 minutes to prevent rate limits
        if self.cached_stories and (now - self.last_fetch_time) < 120:
            return self.cached_stories[:limit]

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        stories: List[NewsStory] = []
        try:
            req = urllib.request.Request(feed_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                xml_data = resp.read()
                tree = ET.fromstring(xml_data)
                items = tree.findall("./channel/item")

                for item in items:
                    title_elem = item.find("title")
                    if title_elem is None or not title_elem.text:
                        continue
                    raw_title = title_elem.text.strip()

                    source_elem = item.find("source")
                    source_name = source_elem.text.strip() if source_elem is not None and source_elem.text else "Live Wire"

                    pub_elem = item.find("pubDate")
                    pub_str = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""

                    # Extract story photo URL from RSS media tags or description HTML
                    # Google News uses Yahoo MRSS namespace: {http://search.yahoo.com/mrss/}
                    img_url = ""
                    mrss_ns = "{http://search.yahoo.com/mrss/}"
                    for child in item:
                        tag = child.tag.lower() if isinstance(child.tag, str) else ""
                        full_tag = child.tag if isinstance(child.tag, str) else ""
                        # Check standard and namespaced media tags
                        if ("thumbnail" in tag or "content" in tag or "enclosure" in tag
                                or full_tag == f"{mrss_ns}thumbnail"
                                or full_tag == f"{mrss_ns}content"):
                            url = child.attrib.get("url") or child.attrib.get("href", "")
                            if url and any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp", "image"]):
                                img_url = url
                                break
                    # Also try namespace-aware find
                    if not img_url:
                        thumb_elem = item.find(f"{mrss_ns}thumbnail")
                        if thumb_elem is not None:
                            img_url = thumb_elem.attrib.get("url", "")
                    if not img_url:
                        content_elem = item.find(f"{mrss_ns}content")
                        if content_elem is not None:
                            img_url = content_elem.attrib.get("url", "")
                    # Fallback: extract from description HTML <img src="...">
                    if not img_url:
                        desc_text = item.findtext("description") or ""
                        m = re.search(r'<img[^>]+src=[\"\'](https?://[^\"\'> ]+)', desc_text)
                        if m:
                            img_url = m.group(1)

                    story = NewsStory(
                        title=raw_title,
                        source=source_name,
                        category=cat.upper() + " NEWS" if cat != "world" else "BREAKING NEWS",
                        published=pub_str,
                        image_url=img_url
                    )
                    stories.append(story)

            if stories:
                self.cached_stories = stories
                self.last_fetch_time = now
                return stories[:limit]

        except Exception as e:
            # If network request fails, return cached stories or fallback news
            if self.cached_stories:
                return self.cached_stories[:limit]

        # Built-in fallback stories if offline
        fallback = [
            NewsStory(
                title="Global Live Stream Broadcast Network Operational 24/7",
                source="MagicStream Wire",
                category="BREAKING NEWS"
            ),
            NewsStory(
                title="Technology Innovations Accelerate Live Multi-Platform Streaming",
                source="Tech Wire",
                category="TECH NEWS"
            ),
            NewsStory(
                title="Global Markets Monitor Real-Time Economic Indicators",
                source="Financial Times",
                category="BUSINESS"
            ),
        ]
        return fallback[:limit]


class NewsBroadcastStudio:
    """Orchestrates AI anchor lip-sync video, audio bulletins, and TV graphics for Mode 6."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        news_cfg = config.get("streaming", {}).get("mode_6_news", {})
        self.category = news_cfg.get("category", "world")
        self.language = news_cfg.get("language", "en")
        self.tts_enabled = news_cfg.get("tts_enabled", True)
        self.ai_anchor_enabled = news_cfg.get("ai_anchor", True)
        self.fetcher = NewsFetcher(self.category)

        from magicstream.anchor_engine import AnchorEngine
        from magicstream.lipsync import LipSyncEngine
        self.anchor_engine = AnchorEngine()
        self.lipsync_engine = LipSyncEngine()
        self.anchor_engine.ensure_assets()

    def set_category(self, new_category: str) -> None:
        """Dynamically switches active news category (e.g. world, india, technology, business, bbc)."""
        self.category = new_category.lower().strip()
        self.fetcher.category = self.category

    def generate_current_bulletin(
        self,
        story_index: int = 0,
        output_audio_path: str = "audio/news_bulletin.mp3",
        output_svg_path: str = "overlay/breaking_news.svg",
        output_video_path: str = "video/anchor_bulletin.mp4"
    ) -> Dict[str, Any]:
        """
        Generates spoken audio bulletin, mixed broadcast audio bed, speech-driven
        lip-synced AI anchor video, and full-screen TV broadcast SVG lower-third & OTS window.
        """
        stories = self.fetcher.fetch_stories(self.category, limit=10)
        idx = story_index % len(stories)
        active_story = stories[idx]

        # Upcoming headlines for bottom ticker
        ticker_items = [s.clean_headline for s in stories[idx+1:idx+6]]
        if not ticker_items:
            ticker_items = [s.clean_headline for s in stories[:4]]

        # 1. Resolve & Download Real News Story Photograph (with Category Fallback)
        story_photo_path = "overlay/current_story_photo.jpg"
        photo_resolved = False

        if active_story.image_url:
            try:
                headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
                req = urllib.request.Request(active_story.image_url, headers=headers)
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    p_data = resp.read()
                    if len(p_data) > 1000:
                        with open(story_photo_path, "wb") as pf:
                            pf.write(p_data)
                        photo_resolved = True
            except Exception as photo_err:
                # Log the failure so we can debug OTS image issues
                import logging
                logging.getLogger("magicstream").debug(
                    f"Photo download failed for '{active_story.image_url[:80]}': {photo_err}"
                )
                photo_resolved = False

        if not photo_resolved:
            topic_plate = f"overlay/topics/{active_story.topic}.jpg"
            if os.path.exists(topic_plate):
                story_photo_path = topic_plate
            else:
                story_photo_path = "overlay/topics/breaking.jpg"

        # 2. Generate Authentic TV Broadcast Lower-Third & OTS Media Window Overlay
        OverlayGenerator.generate_news_lower_third(
            headline=active_story.clean_headline,
            category=active_story.category,
            source=active_story.source,
            ticker_items=ticker_items,
            image_path=story_photo_path,
            topic=active_story.topic,
            output_path=output_svg_path
        )

        # 2. Generate Audio Speech Bulletin with Studio-Grade Neural Broadcast Voices
        raw_audio_file = output_audio_path
        if self.tts_enabled:
            speech_text = (
                f"Breaking News from {active_story.source}. "
                f"{active_story.clean_headline}. "
                f"Updates continue live on MagicStream Studio."
            )
            success = self.anchor_engine.generate_speech(
                text=speech_text,
                output_path=output_audio_path,
                category=self.category,
                language=self.language,
                rate="+6%"
            )
            if not success or not os.path.exists(output_audio_path):
                raw_audio_file = "audio/news_ambient.aac"
        else:
            raw_audio_file = "audio/news_ambient.aac"

        # 3. Mix Broadcast Audio Bed (Vocal EQ + Ambient TV Newsroom Music Bed)
        mixed_audio_path = "audio/news_broadcast_mixed.aac"
        final_audio_path = self.anchor_engine.mix_broadcast_audio(
            speech_path=raw_audio_file,
            output_path=mixed_audio_path,
            ambient_volume=0.16
        )

        # 4. Generate AI Anchorwoman Video with Speech-Driven Lip-Sync & Embedded TV Graphics
        final_video_path = output_video_path
        has_embedded_overlay = False
        png_overlay_path = output_svg_path[:-4] + ".png" if output_svg_path.endswith(".svg") else output_svg_path
        overlay_to_embed = png_overlay_path if os.path.exists(png_overlay_path) else None

        if self.ai_anchor_enabled and os.path.exists(final_audio_path):
            try:
                final_video_path = self.lipsync_engine.generate_synced_video(
                    audio_path=final_audio_path,
                    output_video_path=output_video_path,
                    overlay_path=overlay_to_embed,
                    video_bitrate="2500k"
                )
                has_embedded_overlay = (overlay_to_embed is not None)
            except Exception:
                final_video_path = "video/anchor_speaking_loop.mp4"
                if not os.path.exists(final_video_path):
                    final_video_path = self.config.get("streaming", {}).get("mode_6_news", {}).get("video_path", "video/vid.mp4")

        return {
            "story": active_story,
            "headline": active_story.clean_headline,
            "source": active_story.source,
            "category": active_story.category,
            "svg_path": output_svg_path,
            "png_path": png_overlay_path,
            "has_embedded_overlay": has_embedded_overlay,
            "audio_path": final_audio_path,
            "video_path": final_video_path,
            "stinger_video": self.anchor_engine.get_stinger_clip(),
            "total_stories": len(stories),
            "story_index": idx + 1
        }

