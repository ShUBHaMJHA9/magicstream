"""
FastAPI REST API & Interactive Web Dashboard
Author: Shubham Kumar Jha
License: MIT

Provides HTTP endpoints and a clean real-time web interface
for remote stream monitoring, control, adaptive quality switching, and orchestration.
"""

from typing import Optional, Dict, Any
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel
except ImportError:
    FastAPI = None
    HTTPException = Exception
    HTMLResponse = None
    JSONResponse = None
    class BaseModel:
        pass

from core.streamer import LiveStreamManager
from core.hardware import HardwareDetector, QUALITY_PROFILES


class StartStreamRequest(BaseModel):
    mode: Optional[str] = None
    platform: Optional[str] = None
    stream_key: Optional[str] = None
    source_url: Optional[str] = None
    profile: Optional[str] = None


class SwitchModeRequest(BaseModel):
    mode: str


class SetQualityRequest(BaseModel):
    profile: str  # "auto", "ultra_low", "low", "medium", "high"


def create_api_app(streamer: LiveStreamManager) -> Any:
    """Factory creating configured FastAPI instance attached to stream manager."""
    if FastAPI is None:
        return None
    app = FastAPI(
        title="YT_LIVE Control Center",
        description="Professional multi-platform live streaming API and controller with adaptive quality.",
        version="2.0.0",
    )

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Interactive Web Dashboard with live status, hardware metrics, and controls."""
        status = streamer.get_status()
        is_running = status["is_running"]
        status_badge = '<span style="color: #22c55e; font-weight: bold;">● LIVE STREAMING</span>' if is_running else '<span style="color: #ef4444; font-weight: bold;">● OFFLINE</span>'
        profile_info = status.get("profile_info", {})
        profile_name = profile_info.get("name", status.get("active_profile", "Auto"))

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>YT_LIVE Stream Control Center</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                body {{ background: #0f172a; color: #f8fafc; padding: 2rem; display: flex; justify-content: center; }}
                .container {{ max-width: 950px; width: 100%; }}
                .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 1.5rem; margin-bottom: 2rem; }}
                h1 {{ font-size: 1.8rem; font-weight: 800; background: linear-gradient(135deg, #ff0033, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
                .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.25rem; }}
                .card-title {{ font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }}
                .card-value {{ font-size: 1.35rem; font-weight: 700; color: #f1f5f9; }}
                .card-sub {{ font-size: 0.8rem; color: #64748b; margin-top: 0.35rem; }}
                .controls {{ display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap; }}
                button {{ border: none; border-radius: 8px; padding: 0.8rem 1.6rem; font-size: 0.95rem; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }}
                .btn-start {{ background: #22c55e; color: #052e16; }}
                .btn-start:hover {{ background: #16a34a; color: #ffffff; }}
                .btn-stop {{ background: #ef4444; color: #450a0a; }}
                .btn-stop:hover {{ background: #dc2626; color: #ffffff; }}
                .log-box {{ background: #020617; border: 1px solid #1e293b; border-radius: 12px; padding: 1rem; font-family: monospace; font-size: 0.85rem; color: #cbd5e1; height: 300px; overflow-y: auto; white-space: pre-wrap; }}
                .badge {{ font-size: 0.9rem; padding: 0.3rem 0.8rem; border-radius: 20px; background: #020617; border: 1px solid #334155; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div>
                        <h1>YT_LIVE Control Center</h1>
                        <p style="color: #64748b; font-size: 0.9rem; margin-top: 0.3rem;">Professional Live Broadcast Engine with Adaptive Hardware Protection by Shubham Kumar Jha</p>
                    </div>
                    <div class="badge">{status_badge}</div>
                </div>

                <div class="grid">
                    <div class="card">
                        <div class="card-title">Active Mode</div>
                        <div class="card-value">{status['mode']}</div>
                        <div class="card-sub">Platform: <b style="text-transform: capitalize; color: #38bdf8;">{status['platform']}</b></div>
                    </div>
                    <div class="card">
                        <div class="card-title">Active Quality Profile</div>
                        <div class="card-value" style="color: #38bdf8;">{profile_name}</div>
                        <div class="card-sub">Auto-Downgrade on lag: <b style="color: #22c55e;">Active</b></div>
                    </div>
                    <div class="card">
                        <div class="card-title">Hardware Detection</div>
                        <div class="card-value">{status['system_ram_mb']} MB RAM</div>
                        <div class="card-sub">Cores: {status['cpu_cores']} vCPU | Container Safe</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Stream Uptime</div>
                        <div class="card-value">{status['uptime_formatted']}</div>
                        <div class="card-sub">Reconnects: {status['retries']}</div>
                    </div>
                </div>

                <div class="card" style="margin-bottom: 2rem;">
                    <div class="card-title">Now Playing Media Source</div>
                    <div style="font-size: 1.05rem; font-weight: 600; color: #e2e8f0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        {status['current_media']}
                    </div>
                </div>

                <div class="controls">
                    <button class="btn-start" onclick="fetch('/start', {{method: 'POST'}}).then(() => location.reload())">▶ Start Stream</button>
                    <button class="btn-stop" onclick="fetch('/stop', {{method: 'POST'}}).then(() => location.reload())">⏹ Stop Stream</button>
                    <button style="background: #0284c7; color: #ffffff;" onclick="fetch('/next', {{method: 'POST'}}).then(() => location.reload())">⏭ Next Track</button>
                    <button style="background: #d97706; color: #ffffff;" onclick="fetch('/toggle-shuffle', {{method: 'POST'}}).then(() => location.reload())">🔀 Toggle Shuffle</button>
                    <button style="background: #334155; color: #f8fafc;" onclick="location.reload()">🔄 Refresh</button>
                    <a href="/docs" target="_blank" style="align-self: center; color: #38bdf8; text-decoration: none; font-size: 0.95rem; margin-left: auto;">API Documentation (Swagger) →</a>
                </div>

                <h3 style="margin-bottom: 0.75rem; font-size: 1.1rem; color: #cbd5e1;">Live Stream Telemetry & Logs</h3>
                <div class="log-box" id="logs">Loading telemetry logs...</div>
            </div>

            <script>
                function fetchLogs() {{
                    fetch('/logs').then(r => r.json()).then(data => {{
                        const box = document.getElementById('logs');
                        box.textContent = data.logs.join('\\n');
                        box.scrollTop = box.scrollHeight;
                    }}).catch(console.error);
                }}
                fetchLogs();
                setInterval(fetchLogs, 3000);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    @app.get("/status")
    async def get_status():
        """Retrieve real-time streaming status metrics."""
        return streamer.get_status()

    @app.get("/hardware")
    async def get_hardware():
        """Retrieve detected hardware specs and recommended profile."""
        return HardwareDetector.get_system_summary()

    @app.post("/start")
    async def start_stream(req: Optional[StartStreamRequest] = None):
        """Start streaming with optional mode, profile, and platform overrides."""
        mode = req.mode if req else None
        profile = req.profile if req else None
        if req and req.platform:
            streamer.config_manager.config["destination"]["platform"] = req.platform
        if req and req.stream_key:
            streamer.config_manager.config["destination"]["stream_key"] = req.stream_key
        if req and req.source_url:
            if mode == "mode_2_yt_relay":
                streamer.config_manager.config["streaming"]["mode_2_yt_relay"]["youtube_source_url"] = req.source_url
            elif mode == "mode_5_direct_relay":
                streamer.config_manager.config["streaming"]["mode_5_direct_relay"]["input_stream_url"] = req.source_url

        success = streamer.start(mode=mode, profile=profile)
        if success:
            return JSONResponse(status_code=200, content={"message": "Stream started successfully", "status": streamer.get_status()})
        return JSONResponse(status_code=400, content={"message": "Stream is already running or could not be started."})

    @app.post("/stop")
    async def stop_stream():
        """Stop active stream."""
        success = streamer.stop()
        if success:
            return JSONResponse(status_code=200, content={"message": "Stream stopped successfully."})
        return JSONResponse(status_code=400, content={"message": "Stream is not currently running."})

    @app.get("/health")
    async def healthcheck():
        """Service health check for container orchestrators."""
        return {"status": "healthy", "service": "YT_LIVE", "streaming": streamer.is_running}

    @app.get("/logs")
    async def get_logs():
        """Fetch latest stream log lines."""
        return {"logs": list(streamer.recent_logs)}

    @app.post("/set-quality")
    async def set_quality(req: SetQualityRequest):
        """Dynamically set the active quality profile."""
        profile = req.profile.lower().strip()
        if profile not in QUALITY_PROFILES and profile != "auto":
            raise HTTPException(status_code=400, detail=f"Unknown profile: {profile}. Choose from: auto, {list(QUALITY_PROFILES.keys())}")

        was_running = streamer.is_running
        if was_running:
            streamer.stop()

        if profile == "auto":
            streamer.active_profile_name = HardwareDetector.auto_detect_profile()
        else:
            streamer.active_profile_name = profile

        if was_running:
            streamer.start()

        return {"message": f"Quality profile set to {streamer.active_profile_name}", "profile_info": QUALITY_PROFILES.get(streamer.active_profile_name)}

    @app.post("/switch-mode")
    async def switch_mode(req: SwitchModeRequest):
        """Switch mode on the fly (restarts stream if running)."""
        was_running = streamer.is_running
        if was_running:
            streamer.stop()
        streamer.current_mode = req.mode
        streamer.config_manager.config["streaming"]["mode"] = req.mode
        if was_running:
            streamer.start()
        return {"message": f"Switched mode to {req.mode}", "running": streamer.is_running}

    @app.post("/next")
    async def next_track():
        """Skip currently playing track immediately."""
        success = streamer.skip_track()
        if success:
            return {"message": "Advancing to next track..."}
        return JSONResponse(status_code=400, content={"message": "No active track to skip or stream is not running."})

    @app.post("/toggle-shuffle")
    async def toggle_shuffle():
        """Toggle between random shuffle and sequential playback order."""
        new_order = "sequential" if streamer.playback_order == "random" else "random"
        streamer.playback_order = new_order
        streamer.config_manager.config["streaming"]["playback_order"] = new_order
        return {"message": f"Playback order set to {new_order}", "playback_order": new_order}

    return app
