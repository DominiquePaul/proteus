# 🔱 Proteus

**Shape-shifting video converter** — Transform formats and compress with ease.

Named after the Greek god who could change into any shape at will.

---

## Quick Start

```bash
# Install (one-time)
brew install ffmpeg
uv tool install git+https://github.com/DominiquePaul/proteus.git

# Compress a video
proteus compress path/to/video.mp4
```

**Example output:**
```
🔱 video.mp4 → video_compressed.mp4
   1.0 GB → ~243.6 MB estimated  (⚡ hardware)
📦 Add --slow for ~20% smaller files (5-10x slower)
Tip: Use proteus compress video.mp4 -l heavy for smaller files
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:50
✓ Done  1.0 GB → 197.8 MB  5.1x smaller  (saved 817.0 MB)
📉 Compress further: proteus compress 'video.mp4' --slow -r 720 -l heavy -f
```

---

## Commands

### `compress` — Smart Compression

The easiest way to shrink videos. Uses hardware acceleration by default.

```bash
proteus compress video.mp4 -f                  # Default (medium)
proteus compress video.mp4 -l heavy -f         # Smaller file
proteus compress video.mp4 -r 1080 -f          # Scale 4K → 1080p
proteus compress video.mp4 -r 720 -l heavy -f  # Combine options
proteus compress video.mp4 --slow -f           # Best compression (slower)
```

**Compression Levels:**

| Level | Quality | Best For |
|-------|---------|----------|
| `light` | High | Slight reduction, preserve quality |
| `medium` | Good | Balanced (default) |
| `heavy` | Acceptable | Sharing via email/chat |
| `extreme` | Low | When size matters most |

**Options:**
- `-l`, `--level` — Compression level (light/medium/heavy/extreme)
- `-r`, `--resolution` — Scale down (e.g., `-r 1080`, `-r 720`)
- `-f`, `--force` — Overwrite existing file
- `--slow` — Use software encoding (~20% smaller, 5-10x slower)

---

### `convert` — Format Conversion

Convert any video to MP4 with full control over quality.

```bash
proteus convert video.mov -f           # Basic conversion
proteus convert video.mov -q 28 -f     # Lower quality, smaller file
proteus convert video.mov -r 720 -f    # Scale to 720p
proteus convert video.mov --no-audio -f # Remove audio
```

**Quality Guide (CRF 0-51):**

| CRF | Quality | Use Case |
|-----|---------|----------|
| 18 | Visually lossless | Archival |
| 23 | Excellent | Default |
| 28 | Good | Sharing |
| 35 | Low | Previews |

Lower CRF = better quality, bigger file. Each +6 roughly doubles compression.

**Options:**
- `-q`, `--quality` — CRF value (default: 23)
- `-r`, `--resolution` — Scale down
- `-o`, `--output` — Custom output path
- `--no-audio` — Strip audio track
- `-f`, `--force` — Overwrite existing file
- `--slow` — Software encoding for best compression

---

### `speed` — Speed Up or Slow Down

Change video playback speed. Keeps original format by default.

```bash
proteus speed video.mp4 -x 10 -f          # 10x faster
proteus speed video.mp4 -d 30 -f          # Target 30 seconds duration
proteus speed video.mp4 -x 0.5 -f         # Half speed (slow motion)
proteus speed video.mp4 -x 5 --convert -f # Speed up + convert to MP4
```

**Options:**
- `-x`, `--factor` — Speedup factor (e.g., `-x 10` for 10x faster)
- `-d`, `--duration` — Target duration in seconds
- `-c`, `--convert` — Convert to MP4 H.264 (default: keep original format)
- `--no-audio` — Remove audio track
- `-f`, `--force` — Overwrite existing file

Note: Use either `-x` or `-d`, not both.

---

### `info` — Video Information

```bash
proteus info video.mp4
```

**Example output:**
```
      🎬 video.mp4
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Property    ┃ Value           ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Size        │ 1014.8 MB       │
│ Duration    │ 2:08            │
│ Format      │ QuickTime / MOV │
│ Video Codec │ hevc            │
│ Resolution  │ 3840x2160       │
│ Frame Rate  │ 60.0 fps        │
│ Audio Codec │ aac             │
│ Sample Rate │ 48000 Hz        │
│ Channels    │ 2               │
└─────────────┴─────────────────┘
```

---

### `sizes` — Preview Compression Options

See estimated file sizes before committing to a long encode.

```bash
proteus sizes video.mp4
```

---

### `docs` / `readme` — Open Documentation

```bash
proteus docs    # Opens this README in browser
proteus readme  # Same thing
```

---

## Real-World Examples

### Compress 4K video for sharing

```bash
proteus compress video.mp4 -r 1080 -l heavy -f
```
Result: 1.0 GB → 94.8 MB (10.7x smaller)

### Maximum compression

```bash
proteus compress video.mp4 -r 720 -l extreme --slow -f
```
Result: 1.0 GB → 10.8 MB (93.8x smaller)

### Quick conversion (hardware accelerated)

```bash
proteus compress video.mp4 -f
```
~2 minutes for a 1GB 4K video on Apple Silicon

### Create timelapse from long video

```bash
proteus speed video.mp4 -x 10 -f
```
A 10-minute video becomes 1 minute at 10x speed.

### Batch convert

```bash
for f in *.mov; do proteus compress "$f" -f; done
```

---

## Hardware vs Software Encoding

| Mode | Speed | File Size | When to Use |
|------|-------|-----------|-------------|
| Default (hardware) | ⚡ Fast | Larger | Quick conversions |
| `--slow` (software) | 🐢 5-10x slower | ~20% smaller | When size matters |

Hardware encoding uses Apple VideoToolbox (Mac) for both decoding and encoding.

---

## Tips

1. **Always use `-f`** to overwrite existing files
2. **Start with defaults**, then add `-l heavy` or `-r 720` if needed
3. **Use `proteus sizes`** to preview options before long encodes
4. **Forgot options?** Run `proteus compress --help`

---

## Install / Update / Uninstall

```bash
# Install
uv tool install git+https://github.com/DominiquePaul/proteus.git

# Update (after code changes)
cd /path/to/proteus
uv tool install . --reinstall

# Uninstall
uv tool uninstall proteus
```

**Requires:** [ffmpeg](https://formulae.brew.sh/formula/ffmpeg) (`brew install ffmpeg`)

---

## Why "Proteus"?

In Greek mythology, Proteus was the "Old Man of the Sea" who could transform into any shape. The word *protean* means "versatile" or "capable of assuming many forms."

Perfect for a tool that transforms videos. 🔱
