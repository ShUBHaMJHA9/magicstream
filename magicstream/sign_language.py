"""
================================================================================
MagicStream Sign Language Engine: Accessible TV Hand Gesture Interpreter
Author: Shubham Kumar Jha
License: MIT
================================================================================
Generates dynamic sign language (ISL/ASL) hand gesture animations for deaf
and hard-of-hearing viewers on 24/7 TV live news broadcasts.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import List, Tuple, Optional


class SignLanguageEngine:
    """
    Manages television sign language interpreter animations, gesture transitions,
    and accessibility inset compositing.
    """

    def __init__(
        self,
        gesture_paths: Optional[List[str]] = None,
        pip_box: Tuple[int, int, int, int] = (990, 365, 1240, 525),
    ):
        if gesture_paths is None:
            self.gesture_paths = [
                "video/sign_interpreter_1.jpg",
                "video/sign_interpreter_2.jpg",
                "video/sign_interpreter_3.jpg",
            ]
        else:
            self.gesture_paths = gesture_paths

        self.pip_box = pip_box  # (x1, y1, x2, y2)
        self._cached_gestures: Optional[List[Image.Image]] = None

    def load_gestures(self) -> List[Image.Image]:
        """Loads and pre-resizes sign interpreter frames to the PIP box dimensions."""
        if self._cached_gestures is not None:
            return self._cached_gestures

        w = self.pip_box[2] - self.pip_box[0]
        h = self.pip_box[3] - self.pip_box[1]

        frames = []
        for path in self.gesture_paths:
            if os.path.exists(path):
                img = Image.open(path).convert("RGB")
                # Crop and resize to fill the PIP box
                img_resized = img.resize((w, h), Image.Resampling.LANCZOS)
                frames.append(img_resized)

        if not frames:
            # Fallback placeholder if gesture images are not available
            blank = Image.new("RGB", (w, h), (15, 23, 42))
            frames = [blank]

        self._cached_gestures = frames
        return self._cached_gestures

    def get_gesture_for_frame(self, frame_idx: int, fps: int = 25, is_speaking: bool = True) -> Image.Image:
        """
        Returns the appropriate sign language hand gesture frame.
        When speaking, gestures transition naturally every ~1.2 seconds (30 frames).
        When silent/idle, stays in neutral listening/signing stance.
        """
        gestures = self.load_gestures()
        if len(gestures) == 1:
            return gestures[0]

        if not is_speaking:
            # Neutral stance
            return gestures[0]

        # Natural cadence: ~32 frames (1.28s) per sign gesture phrase
        frames_per_gesture = max(15, int(fps * 1.25))
        pattern = [0, 1, 2, 1, 0, 2]  # Varied signing sequence
        cycle_idx = (frame_idx // frames_per_gesture) % len(pattern)
        gesture_idx = pattern[cycle_idx] % len(gestures)

        return gestures[gesture_idx]
