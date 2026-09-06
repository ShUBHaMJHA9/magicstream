# Logo & Watermark Directory (`logo/`)

This directory is dedicated to storing watermark graphics (logos, corner bugs, channel badges) that are dynamically overlaid onto your live stream in real-time.

## Supported Formats
- **Vector SVG** (`.svg`): Scalable to any resolution (1080p, 720p, 4K) without pixelation or loss of crispness.
- **Transparent PNG** (`.png`): Raster image with alpha transparency.
- **JPEG** (`.jpg`, `.jpeg`): Standard raster image.

## Default Logo
The project includes a pre-built modern broadcast badge:
- File: `logo/logo.svg`
- Resolution: 280x80 (Scalable vector)
- Features: Glowing pulsing LIVE indicator, high-contrast typography, semi-transparent backdrop.

## Watermark Overlay Options

You can configure logo overlay positioning and appearance in `config.yaml` or via CLI parameters:

```yaml
overlay:
  enable: true
  logo_path: "logo/logo.svg"
  # Positions: top-right, top-left, bottom-right, bottom-left, center
  position: "top-right"
  margin_x: 30       # Horizontal margin in pixels
  margin_y: 30       # Vertical margin in pixels
  scale_width: 220   # Overlay width in pixels (maintains aspect ratio, or -1 for native)
  opacity: 0.90      # Transparency (0.1 to 1.0)
```

### Position Coordinates in FFmpeg
- **`top-right`**: `x=W-w-margin_x:y=margin_y`
- **`top-left`**: `x=margin_x:y=margin_y`
- **`bottom-right`**: `x=W-w-margin_x:y=H-h-margin_y`
- **`bottom-left`**: `x=margin_x:y=H-h-margin_y`
- **`center`**: `x=(W-w)/2:y=(H-h)/2`

## Replacing with Your Own Logo
Simply drop your logo file into this `logo/` folder (e.g. `logo/my_channel.svg` or `logo/brand.png`) and update the path in `config.yaml` or run with:
```bash
magicstream --logo logo/brand.png --logo-pos top-right
```
