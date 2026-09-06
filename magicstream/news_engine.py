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

                    story = NewsStory(
                        title=raw_title,
                        source=source_name,
                        category=cat.upper() + " NEWS" if cat != "world" else "BREAKING NEWS",
                        published=pub_str
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
    """Orchestrates audio bulletins, dynamic lower-thirds, and news assets for Mode 6."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        news_cfg = config.get("streaming", {}).get("mode_6_news", {})
        self.category = news_cfg.get("category", "world")
        self.language = news_cfg.get("language", "en")
        self.tts_enabled = news_cfg.get("tts_enabled", True)
        self.fetcher = NewsFetcher(self.category)

    def generate_current_bulletin(
        self,
        story_index: int = 0,
        output_audio_path: str = "audio/news_bulletin.mp3",
        output_svg_path: str = "overlay/breaking_news.svg"
    ) -> Dict[str, Any]:
        """
        Generates spoken audio bulletin and matching breaking news SVG lower-third.
        Returns metadata about the active story.
        """
        stories = self.fetcher.fetch_stories(self.category, limit=10)
        idx = story_index % len(stories)
        active_story = stories[idx]

        # Upcoming headlines for bottom ticker
        ticker_items = [s.clean_headline for s in stories[idx+1:idx+5]]
        if not ticker_items:
            ticker_items = [s.clean_headline for s in stories[:3]]

        # 1. Generate Broadcast Lower-Third Overlay
        OverlayGenerator.generate_news_lower_third(
            headline=active_story.clean_headline,
            category=active_story.category,
            source=active_story.source,
            ticker_items=ticker_items,
            output_path=output_svg_path
        )

        # 2. Generate Audio Speech Bulletin (if TTS enabled)
        audio_file = output_audio_path
        if self.tts_enabled and HAS_GTTS:
            try:
                os.makedirs(os.path.dirname(output_audio_path) or ".", exist_ok=True)
                speech_text = (
                    f"Breaking News from {active_story.source}. "
                    f"{active_story.clean_headline}. "
                    f"Updates continue live on MagicStream Studio."
                )
                tts = gTTS(speech_text, lang=self.language, slow=False)
                tts.save(output_audio_path)
            except Exception:
                # Fallback to default ambient audio if TTS generation encounters network delay
                audio_file = self.config.get("streaming", {}).get("mode_6_news", {}).get("ambient_audio", "audio/news_ambient.mp3")
                if not os.path.exists(audio_file):
                    audio_file = self.config.get("streaming", {}).get("mode_1_radio", {}).get("audio_source", "audio/audio.txt")
        else:
            audio_file = self.config.get("streaming", {}).get("mode_6_news", {}).get("ambient_audio", "audio/news_ambient.mp3")

        return {
            "story": active_story,
            "headline": active_story.clean_headline,
            "source": active_story.source,
            "category": active_story.category,
            "svg_path": output_svg_path,
            "audio_path": audio_file,
            "total_stories": len(stories),
            "story_index": idx + 1
        }
