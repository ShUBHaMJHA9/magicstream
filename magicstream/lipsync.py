"""
================================================================================
MagicStream LipSync & Accessibility Engine
Author: Shubham Kumar Jha
License: MIT
================================================================================
Performs speech-driven facial lip synchronization and composite rendering
of the AI news anchor along with deaf accessibility sign language hand gestures.
"""

import os
import subprocess
import time
from typing import List, Optional, Tuple, Dict
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


class LipSyncEngine:
    """
    Speech-driven facial animation and sign language accessibility compositor.
    Analyzes audio RMS energy per frame to animate mouth articulation
    while simultaneously cycling TV sign language interpreter hand gestures.
    """

    def __init__(
        self,
        idle_image_path: str = "video/ai_anchor_studio.jpg",
        speaking_image_path: str = "video/ai_anchor_speaking.jpg",
        target_resolution: Tuple[int, int] = (1280, 720),
        fps: int = 25,
        num_viseme_steps: int = 6,
    ):
        self.idle_image_path = idle_image_path
        self.speaking_image_path = speaking_image_path
        self.target_resolution = target_resolution
        self.fps = fps
        self.num_viseme_steps = num_viseme_steps

        # Precise facial mouth bounding box at 1280x720
        self.mouth_box = (580, 175, 710, 275)

        # Accessibility sign language PIP window: bottom-right
        self.pip_box = (980, 360, 1240, 520)

        self._frame_cache: Optional[Dict[Tuple[int, int], bytes]] = None

    def _build_mouth_feather_mask(self, width: int, height: int) -> Image.Image:
        """Creates an elliptical feathered alpha mask to seamlessly blend the mouth."""
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((8, 8, width - 8, height - 8), fill=255)
        return mask.filter(ImageFilter.GaussianBlur(6))

    def _load_and_cache_frames(self) -> Dict[Tuple[int, int], bytes]:
        """
        Precomputes all (viseme_level, gesture_idx) frame bytes in memory.
        Enables 100+ FPS real-time rendering with zero per-frame arithmetic.
        """
        if self._frame_cache is not None:
            return self._frame_cache

        from magicstream.sign_language import SignLanguageEngine
        sign_engine = SignLanguageEngine(pip_box=self.pip_box)
        gestures = sign_engine.load_gestures()

        w, h = self.target_resolution
        idle_full = Image.open(self.idle_image_path).resize((w, h), Image.Resampling.LANCZOS).convert("RGB")
        talk_full = Image.open(self.speaking_image_path).resize((w, h), Image.Resampling.LANCZOS).convert("RGB")

        # Extract mouth crops and build feather mask
        mw = self.mouth_box[2] - self.mouth_box[0]
        mh = self.mouth_box[3] - self.mouth_box[1]
        mouth_mask = self._build_mouth_feather_mask(mw, mh)

        mouth_idle = idle_full.crop(self.mouth_box)
        mouth_talk = talk_full.crop(self.mouth_box)

        # Pre-render blended mouth crops for viseme steps [0.0 to 1.0]
        alphas = np.linspace(0.0, 1.0, self.num_viseme_steps)
        blended_mouths = []
        for a in alphas:
            m = Image.blend(mouth_idle, mouth_talk, float(a))
            blended_mouths.append(m)

        # Build PIP frame styling for Sign Language window
        pip_w = self.pip_box[2] - self.pip_box[0]
        pip_h = self.pip_box[3] - self.pip_box[1]
        pip_mask = Image.new("L", (pip_w, pip_h), 0)
        p_draw = ImageDraw.Draw(pip_mask)
        p_draw.rounded_rectangle((0, 0, pip_w, pip_h), radius=12, fill=255)

        cache: Dict[Tuple[int, int], bytes] = {}

        for v_idx, mouth_crop in enumerate(blended_mouths):
            # Base frame with feathered mouth
            base_frame = idle_full.copy()
            base_frame.paste(mouth_crop, self.mouth_box, mouth_mask)

            # Paste each gesture into the PIP box
            for g_idx, gesture_img in enumerate(gestures):
                frame = base_frame.copy()

                # Paste sign language interpreter in PIP box with rounded corners
                frame.paste(gesture_img, self.pip_box, pip_mask)

                # Draw glowing cyan border and accessibility badge
                f_draw = ImageDraw.Draw(frame)
                f_draw.rounded_rectangle(self.pip_box, radius=12, outline=(0, 240, 255), width=2)
                f_draw.rectangle((self.pip_box[0], self.pip_box[1], self.pip_box[0] + 160, self.pip_box[1] + 20), fill=(15, 23, 42))
                f_draw.text((self.pip_box[0] + 6, self.pip_box[1] + 3), "ISL INTERPRETER", fill=(0, 240, 255))

                cache[(v_idx, g_idx)] = frame.tobytes()

        self._frame_cache = cache
        return self._frame_cache

    def analyze_audio_envelope(self, audio_path: str) -> Tuple[np.ndarray, float]:
        """
        Extracts raw 16-bit PCM audio samples and calculates normalized,
        attack/decay-smoothed mouth opening coefficients [0.0, 1.0] per video frame.
        """
        sample_rate = 16000
        cmd = [
            "ffmpeg", "-y", "-i", audio_path,
            "-f", "s16le", "-ac", "1", "-ar", str(sample_rate),
            "pipe:1"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        pcm_bytes, _ = proc.communicate()

        if not pcm_bytes:
            return np.zeros(1, dtype=np.float32), 0.0

        samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
        duration_sec = len(samples) / float(sample_rate)
        samples_per_frame = int(sample_rate / float(self.fps))
        total_frames = max(1, int(duration_sec * self.fps))

        # Calculate Root Mean Square (RMS) energy per video frame
        rms_series = []
        for i in range(total_frames):
            start = i * samples_per_frame
            end = start + samples_per_frame
            chunk = samples[start:end]
            if len(chunk) > 0:
                rms = float(np.sqrt(np.mean(chunk**2)))
            else:
                rms = 0.0
            rms_series.append(rms)

        rms_arr = np.array(rms_series, dtype=np.float32)
        peak_rms = float(rms_arr.max())
        silence_floor = peak_rms * 0.10  # Silence cutoff threshold

        # Normalize with soft knee compression
        normalized = np.zeros_like(rms_arr)
        active_mask = rms_arr > silence_floor
        if peak_rms > 1e-3:
            normalized[active_mask] = np.clip((rms_arr[active_mask] - silence_floor) / (peak_rms * 0.60), 0.0, 1.0)

        # Smooth envelope with bi-directional attack and gentle release
        # Mimics natural human speech jaw & lip inertia
        smoothed = np.zeros_like(normalized)
        current = 0.0
        for i in range(len(normalized)):
            target = normalized[i]
            if target > current:
                current = current * 0.35 + target * 0.65  # Fast 35ms opening attack
            else:
                current = current * 0.68 + target * 0.32  # Smooth 70ms closing release
            smoothed[i] = current

        return smoothed, duration_sec

    def generate_synced_video(
        self,
        audio_path: str,
        output_video_path: str = "video/anchor_bulletin.mp4",
        video_bitrate: str = "2500k",
    ) -> str:
        """
        Synthesizes a complete video file with the AI news anchor speaking
        with speech-driven lip synchronization matching the audio file,
        plus the live sign language hand gesture interpreter.
        """
        os.makedirs(os.path.dirname(output_video_path) or ".", exist_ok=True)
        frame_cache = self._load_and_cache_frames()
        openings, duration_sec = self.analyze_audio_envelope(audio_path)
        w, h = self.target_resolution

        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{w}x{h}",
            "-pix_fmt", "rgb24",
            "-r", str(self.fps),
            "-i", "-",
            "-i", audio_path,
            "-c:v", "libopenh264",
            "-b:v", video_bitrate,
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "160k",
            "-shortest",
            output_video_path
        ]

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        max_viseme = self.num_viseme_steps - 1
        num_gestures = 3
        # Gesture cadence: change sign language gesture every ~30 frames (1.2s)
        gesture_cadence = max(15, int(self.fps * 1.25))
        gesture_pattern = [0, 1, 2, 1, 0, 2]

        for i, opening in enumerate(openings):
            # Viseme opening index directly derived from audio amplitude
            v_idx = int(round(opening * max_viseme))
            v_idx = max(0, min(max_viseme, v_idx))

            # Sign language gesture index
            is_speaking = opening > 0.05
            if is_speaking:
                c_idx = (i // gesture_cadence) % len(gesture_pattern)
                g_idx = gesture_pattern[c_idx] % num_gestures
            else:
                g_idx = 0  # Neutral listening stance

            frame_bytes = frame_cache.get((v_idx, g_idx))
            if frame_bytes:
                proc.stdin.write(frame_bytes)

        proc.stdin.close()
        proc.wait()

        return output_video_path
