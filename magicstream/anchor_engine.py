"""
================================================================================
MagicStream Anchor Engine: AI Virtual Presenter, Lip-Sync & TV Stinger Studio
Author: Shubham Kumar Jha
License: MIT
================================================================================
Orchestrates AI news anchor animation, talking viseme cycles, broadcast audio
mixing (voice EQ + ambient TV news music bed), and ABP News-style stinger alerts.
"""

import os
import re
import subprocess
import time
from typing import Optional, Dict, Any


class AnchorEngine:
    """Manages AI news anchor visual loops, audio bed mixing, and stinger intros."""

    def __init__(
        self,
        idle_image: str = "video/ai_anchor_studio.jpg",
        speaking_image: str = "video/ai_anchor_speaking.jpg",
        stinger_video: str = "video/breaking_stinger.mp4",
        ambient_music: str = "audio/news_ambient.aac",
    ):
        self.idle_image = idle_image
        self.speaking_image = speaking_image
        self.stinger_video = stinger_video
        self.ambient_music = ambient_music
        self.speaking_loop_video = "video/anchor_speaking_loop.mp4"

    def ensure_assets(self) -> bool:
        """Verifies that all AI anchor and broadcast stinger assets exist."""
        os.makedirs("video", exist_ok=True)
        os.makedirs("audio", exist_ok=True)
        os.makedirs("overlay", exist_ok=True)

        if not os.path.exists(self.speaking_loop_video):
            self._create_speaking_loop()

        return os.path.exists(self.speaking_loop_video)

    def _create_speaking_loop(self) -> bool:
        """Builds a 1-second seamless talking animation loop at 30 fps."""
        if not (os.path.exists(self.idle_image) and os.path.exists(self.speaking_image)):
            return False

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", "1.0", "-i", self.idle_image,
            "-loop", "1", "-t", "1.0", "-i", self.speaking_image,
            "-filter_complex",
            "[0:v][1:v]blend=all_expr='if(between(mod(N\\,30)\\,4\\,8)+between(mod(N\\,30)\\,12\\,17)+between(mod(N\\,30)\\,22\\,25)\\,B\\,A)',format=yuv420p[v]",
            "-map", "[v]",
            "-c:v", "libopenh264",
            "-r", "30",
            "-t", "1.0",
            self.speaking_loop_video
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except Exception:
            return False

    def mix_broadcast_audio(
        self,
        speech_path: str,
        output_path: str = "audio/news_broadcast_mixed.aac",
        ambient_volume: float = 0.16
    ) -> str:
        """
        Applies vocal EQ & dynamic compression to the TTS anchor voice, and mixes
        the urgent electronic newsroom music bed underneath at a balanced volume.
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        if not os.path.exists(speech_path):
            return speech_path

        if not os.path.exists(self.ambient_music):
            # No ambient track, return speech directly
            return speech_path

        # FFmpeg filter: Vocal EQ + Newsroom Music Bed
        # [0:a] is speech: highpass 80Hz, lowpass 11kHz, volume boost, compression
        # [1:a] is ambient music: looped, lowered to 16% volume
        filter_str = (
            f"[0:a]highpass=f=80,lowpass=f=11000,volume=1.35,acompressor=threshold=0.12:ratio=3:attack=10:release=150[voice];"
            f"[1:a]aloop=loop=-1:size=2e+09,volume={ambient_volume:.2f}[bed];"
            f"[voice][bed]amix=inputs=2:duration=first:dropout_transition=2,volume=1.1[outa]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", speech_path,
            "-i", self.ambient_music,
            "-filter_complex", filter_str,
            "-map", "[outa]",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            output_path
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=30)
            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 500:
                return output_path
        except Exception:
            pass

        return speech_path

    def get_stinger_clip(self) -> Optional[str]:
        """Returns path to the 3D Breaking News Alert stinger animation video."""
        if os.path.exists(self.stinger_video):
            return self.stinger_video
        return None
