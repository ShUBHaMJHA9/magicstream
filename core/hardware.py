"""
Hardware Capability Detection & Adaptive Quality Profiling
Author: Shubham Kumar Jha
License: MIT

Detects system resources (RAM, container memory limits, CPU cores, cgroup quotas)
and automatically selects or dynamically downgrades video quality profiles to
prevent stream lag, buffering, or OOM crashes on low-end hardware (512MB RAM, 0.1 vCPU).
"""

import os
import re
import sys
from typing import Dict, Any, Tuple


# Predefined Quality Profiles engineered for various resource constraints
QUALITY_PROFILES: Dict[str, Dict[str, Any]] = {
    # Ultra-low resource profile: specifically for 500MB - 1GB container RAM and 0.1 - 0.5 vCPU
    "ultra_low": {
        "name": "Ultra-Low / Container (240p)",
        "resolution": "426x240",
        "fps": 15,
        "preset": "ultrafast",
        "video_bitrate": "250k",
        "max_rate": "300k",
        "buf_size": "500k",
        "gop_size": 30,
        "audio_codec": "aac",
        "audio_bitrate": "64k",
        "audio_sample_rate": 22050,
        "threads": 1,
        "max_logo_width": 100,
    },
    # Low resource profile: 1GB - 1.5GB RAM, 1 vCPU
    "low": {
        "name": "Low-End / Budget VPS (480p)",
        "resolution": "854x480",
        "fps": 24,
        "preset": "superfast",
        "video_bitrate": "800k",
        "max_rate": "1000k",
        "buf_size": "1600k",
        "gop_size": 48,
        "audio_codec": "aac",
        "audio_bitrate": "96k",
        "audio_sample_rate": 44100,
        "threads": 2,
        "max_logo_width": 150,
    },
    # Medium / Standard HD profile: 2GB - 4GB RAM, 2 vCPUs
    "medium": {
        "name": "Standard HD (720p)",
        "resolution": "1280x720",
        "fps": 30,
        "preset": "veryfast",
        "video_bitrate": "2500k",
        "max_rate": "2800k",
        "buf_size": "5000k",
        "gop_size": 60,
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "audio_sample_rate": 44100,
        "threads": 0,  # Auto threads
        "max_logo_width": 200,
    },
    # High resource profile: 4GB+ RAM, 4+ vCPUs or GPU
    "high": {
        "name": "Full HD (1080p)",
        "resolution": "1920x1080",
        "fps": 30,
        "preset": "faster",
        "video_bitrate": "4500k",
        "max_rate": "5000k",
        "buf_size": "9000k",
        "gop_size": 60,
        "audio_codec": "aac",
        "audio_bitrate": "160k",
        "audio_sample_rate": 44100,
        "threads": 0,  # Auto threads
        "max_logo_width": 260,
    },
}

# Profile order for auto-downgrade ladder
PROFILE_LADDER = ["high", "medium", "low", "ultra_low"]


class HardwareDetector:
    """Detects available hardware resources and manages adaptive streaming quality."""

    @staticmethod
    def get_system_ram_mb() -> int:
        """
        Detects available RAM in MB, taking Linux cgroup container limits into account.
        Supports Docker, Kubernetes, LXC, and bare-metal Linux.
        """
        cgroup_limit_mb = None

        # 1. Check cgroup v2 memory limit
        cgroup_v2_path = "/sys/fs/cgroup/memory.max"
        if os.path.exists(cgroup_v2_path):
            try:
                with open(cgroup_v2_path, "r") as f:
                    val = f.read().strip()
                    if val != "max" and val.isdigit():
                        cgroup_limit_mb = int(val) // (1024 * 1024)
            except Exception:
                pass

        # 2. Check cgroup v1 memory limit
        cgroup_v1_path = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
        if cgroup_limit_mb is None and os.path.exists(cgroup_v1_path):
            try:
                with open(cgroup_v1_path, "r") as f:
                    val = f.read().strip()
                    if val.isdigit() and int(val) < (1 << 60):
                        cgroup_limit_mb = int(val) // (1024 * 1024)
            except Exception:
                pass

        # 3. Check system /proc/meminfo
        host_mem_mb = 2048  # Default fallback
        if os.path.exists("/proc/meminfo"):
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            parts = line.split()
                            host_mem_mb = int(parts[1]) // 1024
                            break
            except Exception:
                pass

        if cgroup_limit_mb and cgroup_limit_mb > 0:
            return min(cgroup_limit_mb, host_mem_mb)
        return host_mem_mb

    @staticmethod
    def get_cpu_cores() -> float:
        """
        Detects available CPU count, respecting container CFS quotas if running in Docker.
        """
        # Check cgroup v2 cpu.max
        cgroup_v2_cpu = "/sys/fs/cgroup/cpu.max"
        if os.path.exists(cgroup_v2_cpu):
            try:
                with open(cgroup_v2_cpu, "r") as f:
                    quota, period = f.read().strip().split()
                    if quota != "max" and int(period) > 0:
                        return max(0.1, round(int(quota) / int(period), 2))
            except Exception:
                pass

        # Check cgroup v1 cpu quota
        quota_path = "/sys/fs/cgroup/cpu/cpu.cfs_quota_us"
        period_path = "/sys/fs/cgroup/cpu/cpu.cfs_period_us"
        if os.path.exists(quota_path) and os.path.exists(period_path):
            try:
                with open(quota_path, "r") as fq, open(period_path, "r") as fp:
                    quota = int(fq.read().strip())
                    period = int(fp.read().strip())
                    if quota > 0 and period > 0:
                        return max(0.1, round(quota / period, 2))
            except Exception:
                pass

        # Fallback to host CPU count
        return float(os.cpu_count() or 1)

    @classmethod
    def auto_detect_profile(cls) -> str:
        """
        Selects the best quality profile based on detected RAM and CPU.
        Works seamlessly on low-end servers, 500MB containers, or 16-core workstations.
        """
        ram_mb = cls.get_system_ram_mb()
        cpu_cores = cls.get_cpu_cores()

        # Strict container / ultra-low checks
        if ram_mb <= 800 or cpu_cores <= 0.6:
            return "ultra_low"
        elif ram_mb <= 1600 or cpu_cores <= 1.2:
            return "low"
        elif ram_mb <= 3500 or cpu_cores <= 2.5:
            return "medium"
        else:
            return "high"

    @classmethod
    def get_profile(cls, profile_name: str) -> Dict[str, Any]:
        """Returns quality profile settings by name."""
        name = profile_name.lower().strip()
        if name == "auto":
            name = cls.auto_detect_profile()
        return QUALITY_PROFILES.get(name, QUALITY_PROFILES["medium"])

    @classmethod
    def get_downgraded_profile_name(cls, current_profile_name: str) -> str:
        """Returns the next lower quality profile in the ladder."""
        current = current_profile_name.lower().strip()
        if current not in PROFILE_LADDER:
            return "ultra_low"

        idx = PROFILE_LADDER.index(current)
        if idx + 1 < len(PROFILE_LADDER):
            return PROFILE_LADDER[idx + 1]
        return PROFILE_LADDER[-1]  # Already at lowest (ultra_low)

    @classmethod
    def get_system_summary(cls) -> Dict[str, Any]:
        """Returns hardware report for dashboard and CLI."""
        ram_mb = cls.get_system_ram_mb()
        cpu_cores = cls.get_cpu_cores()
        recommended = cls.auto_detect_profile()

        return {
            "ram_mb": ram_mb,
            "ram_gb": round(ram_mb / 1024, 2),
            "cpu_cores": cpu_cores,
            "recommended_profile": recommended,
            "profile_name": QUALITY_PROFILES[recommended]["name"],
        }
