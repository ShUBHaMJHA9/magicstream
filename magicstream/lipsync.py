"""
================================================================================
MagicStream LipSync & Accessibility Engine
Author: Shubham Kumar Jha
License: MIT
================================================================================
Performs speech-driven facial lip synchronization and composite rendering
of the AI news anchor along with deaf accessibility sign language hand gestures.

Natural Broadcast Lip-Sync:
- 4 viseme states: Closed, Slight, Mid-Open, Full Open
- EMA-smoothed audio envelope (attack=0.30, decay=0.08)
- Minimum 4-frame hold per viseme (~160ms @ 25fps)
- Results in 3-4 transitions/sec matching real TV anchor cadence
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
    Analyzes audio RMS energy per frame with EMA smoothing to animate mouth
    at natural broadcast cadence (3-4 transitions/sec), while simultaneously
    cycling TV sign language interpreter hand gestures.
    """

    # 4 natural broadcast viseme states (cleaner than 6 at 720p)
    NUM_VISEMES = 4
    # Minimum frames a viseme must hold before transitioning (~120ms @ 25fps)
    MIN_HOLD_FRAMES = 3
    # EMA smoothing coefficients for natural jaw inertia (tuned for ~3 transitions/sec)
    EMA_ATTACK = 0.40   # How fast mouth opens on energy rise
    EMA_DECAY = 0.20    # How slowly mouth closes (jaw has inertia)

    def __init__(
        self,
        idle_image_path: str = "video/ai_anchor_studio.jpg",
        speaking_image_path: str = "video/ai_anchor_speaking.jpg",
        target_resolution: Tuple[int, int] = (1280, 720),
        fps: int = 25,
    ):
        self.idle_image_path = idle_image_path
        self.speaking_image_path = speaking_image_path
        self.target_resolution = target_resolution
        self.fps = fps

        # Precise facial mouth bounding box at 1280x720 (tight lips only, eliminating face ghosting)
        self.mouth_box = (612, 236, 684, 274)

        # Accessibility sign language PIP window: bottom-right
        self.pip_box = (980, 360, 1240, 520)

        self._frame_cache: Optional[Dict[Tuple[int, int], bytes]] = None
        self._cached_overlay_id = None

    def _build_mouth_feather_mask(self, width: int, height: int) -> Image.Image:
        """Creates an elliptical feathered alpha mask to seamlessly blend the mouth."""
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((4, 4, width - 4, height - 4), fill=255)
        return mask.filter(ImageFilter.GaussianBlur(3))

    def _load_and_cache_frames(self, overlay_path: Optional[str] = None) -> Dict[Tuple[int, int], bytes]:
        """
        Precomputes all (viseme_level, gesture_idx) frame bytes in memory.
        Uses 4 natural visemes (closed, slight, mid, open) for clean broadcast motion.
        Composites deaf interpreter and television broadcast overlay directly into all frames.
        """
        cache_id = (overlay_path, os.path.getmtime(overlay_path) if overlay_path and os.path.exists(overlay_path) else 0)
        if self._frame_cache is not None and self._cached_overlay_id == cache_id:
            return self._frame_cache

        from magicstream.sign_language import SignLanguageEngine
        sign_engine = SignLanguageEngine(pip_box=self.pip_box)
        gestures = sign_engine.load_gestures()

        w, h = self.target_resolution
        idle_full = Image.open(self.idle_image_path).resize((w, h), Image.Resampling.LANCZOS).convert("RGB")
        talk_full = Image.open(self.speaking_image_path).resize((w, h), Image.Resampling.LANCZOS).convert("RGB")

        # Load optional TV broadcast overlay (OTS window, lower-third, ticker)
        overlay_img = None
        if overlay_path and os.path.exists(overlay_path):
            try:
                overlay_img = Image.open(overlay_path).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
            except Exception:
                overlay_img = None

        # Extract tight mouth crops and build feather mask
        mw = self.mouth_box[2] - self.mouth_box[0]
        mh = self.mouth_box[3] - self.mouth_box[1]
        mouth_mask = self._build_mouth_feather_mask(mw, mh)

        m_closed = idle_full.crop(self.mouth_box)
        m_open = talk_full.crop(self.mouth_box)

        # Build 4 natural broadcast visemes (clean, distinct shapes)
        # v0: Closed neutral mouth (silence, M, B, P)
        v0 = m_closed
        # v1: Slight consonant opening (S, T, D, L) — 30% open
        v1 = Image.blend(m_closed, m_open, 0.30)
        # v2: Mid-range vowel (E, I, short A) — 65% open
        v2 = Image.blend(m_closed, m_open, 0.65)
        # v3: Full open vowel (A, Ah, O, emphasis) — 100% open
        v3 = m_open

        distinct_visemes = [v0, v1, v2, v3]

        # Build PIP frame styling for Sign Language window
        pip_w = self.pip_box[2] - self.pip_box[0]
        pip_h = self.pip_box[3] - self.pip_box[1]
        pip_mask = Image.new("L", (pip_w, pip_h), 0)
        p_draw = ImageDraw.Draw(pip_mask)
        p_draw.rounded_rectangle((0, 0, pip_w, pip_h), radius=12, fill=255)

        cache: Dict[Tuple[int, int], bytes] = {}

        for v_idx, mouth_crop in enumerate(distinct_visemes):
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

                # Composite full TV broadcast graphics overlay if provided
                if overlay_img is not None:
                    frame.paste(overlay_img, (0, 0), overlay_img)

                cache[(v_idx, g_idx)] = frame.tobytes()

        self._frame_cache = cache
        self._cached_overlay_id = cache_id
        return self._frame_cache

    def analyze_audio_syllables(self, audio_path: str) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Natural Broadcast Lip-Sync Analysis:

        1. Extracts 16-bit PCM audio at 16kHz
        2. Computes per-frame RMS energy
        3. Applies EMA smoothing (attack=0.30, decay=0.08) for natural jaw inertia
        4. Maps to 4 visemes: Closed(0), Slight(1), Mid(2), Open(3)
        5. Enforces minimum 4-frame hold per viseme (~160ms)

        Result: 3-4 viseme transitions/sec — matching real TV news anchor cadence.
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
            return np.zeros(1, dtype=int), np.zeros(1, dtype=bool), 0.0

        samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
        duration_sec = len(samples) / float(sample_rate)
        samples_per_frame = int(sample_rate / float(self.fps))
        total_frames = max(1, int(duration_sec * self.fps))

        # ── Step 1: Per-frame RMS energy ──
        rms_series = []
        for i in range(total_frames):
            start = i * samples_per_frame
            end = start + samples_per_frame
            chunk = samples[start:end]
            rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
            rms_series.append(rms)

        rms_arr = np.array(rms_series, dtype=np.float32)
        peak_rms = float(rms_arr.max()) if len(rms_arr) > 0 else 1.0
        if peak_rms < 1e-4:
            return np.zeros(total_frames, dtype=int), np.zeros(total_frames, dtype=bool), duration_sec

        # Normalize to [0, 1] with soft headroom
        norm = np.clip(rms_arr / (peak_rms * 0.70 + 1e-6), 0.0, 1.0)

        # ── Step 2: EMA smoothing for natural jaw inertia ──
        # Mouth opens at attack=0.40, closes at decay=0.20 → ~3 viseme changes/sec
        # This replicates real human jaw biomechanics — opening is fast, closing has inertia
        smoothed = np.zeros_like(norm)
        current = 0.0
        for i in range(total_frames):
            target = norm[i]
            if target > current:
                current = current + self.EMA_ATTACK * (target - current)
            else:
                current = current + self.EMA_DECAY * (target - current)
            smoothed[i] = current

        # ── Step 3: Map smoothed envelope to 4 viseme states ──
        silence_threshold = 0.10
        slight_threshold = 0.30
        mid_threshold = 0.55

        raw_visemes = np.zeros(total_frames, dtype=int)
        is_speaking = np.zeros(total_frames, dtype=bool)

        for i in range(total_frames):
            e = smoothed[i]
            if e < silence_threshold:
                raw_visemes[i] = 0   # Closed
                is_speaking[i] = False
            elif e < slight_threshold:
                raw_visemes[i] = 1   # Slight opening
                is_speaking[i] = True
            elif e < mid_threshold:
                raw_visemes[i] = 2   # Mid-open vowel
                is_speaking[i] = True
            else:
                raw_visemes[i] = 3   # Full open
                is_speaking[i] = True

        # ── Step 4: Temporal hold — enforce minimum hold per viseme ──
        # Prevents rapid flickering: each viseme must hold for at least MIN_HOLD_FRAMES
        final_visemes = np.zeros(total_frames, dtype=int)
        current_viseme = raw_visemes[0]
        hold_counter = 0

        for i in range(total_frames):
            if raw_visemes[i] != current_viseme:
                hold_counter += 1
                if hold_counter >= self.MIN_HOLD_FRAMES:
                    # Enough frames requesting the change — commit the transition
                    current_viseme = raw_visemes[i]
                    hold_counter = 0
            else:
                hold_counter = 0
            final_visemes[i] = current_viseme

        return final_visemes, is_speaking, duration_sec

    def generate_synced_video(
        self,
        audio_path: str,
        output_video_path: str = "video/anchor_bulletin.mp4",
        overlay_path: Optional[str] = None,
        video_bitrate: str = "2500k",
    ) -> str:
        """
        Synthesizes a complete video file with the AI news anchor speaking
        with natural broadcast lip synchronization (3-4 transitions/sec),
        plus the live sign language hand gesture interpreter and TV graphics overlay.
        """
        os.makedirs(os.path.dirname(output_video_path) or ".", exist_ok=True)
        frame_cache = self._load_and_cache_frames(overlay_path=overlay_path)
        visemes, is_speaking_arr, duration_sec = self.analyze_audio_syllables(audio_path)
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

        num_gestures = 6  # 6 smooth gesture steps (g0, g01, g1, g12, g2, g20)
        # Sign interpreter changes pose every ~12 frames (~480ms) for natural motion
        gesture_cadence = 12

        for i in range(len(visemes)):
            v_idx = int(visemes[i])
            is_active = bool(is_speaking_arr[i])

            if is_active:
                # Progress smoothly through sign language interpreter poses
                g_idx = (i // gesture_cadence) % num_gestures
            else:
                g_idx = 0  # Attentive resting stance during breath pauses

            frame_bytes = frame_cache.get((v_idx, g_idx))
            if frame_bytes:
                proc.stdin.write(frame_bytes)

        proc.stdin.close()
        proc.wait()

        return output_video_path
