# 🔱 Proteus

**Shape-shifting video converter** — Transform formats and compress with ease.

Named after the Greek god Proteus, who could change into any shape at will.

---

## Quick Start

```bash
# Install (one-time)
brew install ffmpeg
uv tool install git+https://github.com/DominiquePaul/proteus.git

# Use anywhere
proteus convert video.mov           # → video.mp4
proteus compress video.mp4 -l heavy # → smaller file for sharing
proteus info video.mov              # → show video details
```

---

## Commands

### `convert` — Format Conversion

The workhorse command. Converts any video to MP4 (H.264/AAC).

```bash
# Basic conversion
proteus convert video.mov

# Custom output name
proteus convert video.mov -o output.mp4

# Lower quality for smaller file (CRF 28)
proteus convert video.mov -q 28

# Higher quality (CRF 18)
proteus convert video.mov -q 18

# Scale to 720p (maintains aspect ratio)
proteus convert video.mov -r 720

# Scale to specific resolution
proteus convert video.mov -r 1280x720

# Remove audio
proteus convert video.mov --no-audio

# Combine options
proteus convert video.mov -o small.mp4 -q 28 -r 720
```

**Quality Guide (CRF):**
| CRF | Quality | File Size | Use Case |
|-----|---------|-----------|----------|
| 18 | Excellent | Large | Archival |
| 23 | Good | Medium | Default, general use |
| 28 | Acceptable | Small | Sharing, uploads |
| 32+ | Low | Tiny | Previews, thumbnails |

### `compress` — Smart Compression

Preset-based compression for when you just want "make it smaller."

```bash
# Medium compression (balanced)
proteus compress video.mp4

# Light compression (minimal quality loss)
proteus compress video.mp4 -l light

# Heavy compression (for sharing)
proteus compress video.mp4 -l heavy

# Extreme compression (significant quality loss)
proteus compress video.mp4 -l extreme
```

**Compression Levels:**
| Level | CRF | Best For |
|-------|-----|----------|
| light | 20 | Slight reduction, preserve quality |
| medium | 26 | Good balance |
| heavy | 30 | Sharing via email/chat |
| extreme | 35 | When size matters most |

### `info` — Video Information

Inspect video metadata.

```bash
proteus info video.mov
```

Shows: codec, resolution, duration, file size, frame rate, audio info.

### `formats` — Quick Reference

Show a cheatsheet of common conversions.

```bash
proteus formats
```

### `docs` — Documentation

Render this README beautifully in your terminal.

```bash
proteus docs
```

---

## Common Workflows

### Convert iPhone video for web

```bash
proteus convert IMG_1234.MOV -r 1080 -q 26
```

### Compress for email attachment

```bash
proteus compress presentation.mp4 -l heavy
```

### Batch convert all .mov files

```bash
for f in *.mov; do proteus convert "$f"; done
```

### Make a small preview

```bash
proteus convert video.mov -o preview.mp4 -r 480 -q 32
```

---

## Options Reference

### Global Options

| Option | Description |
|--------|-------------|
| `--help` | Show help for any command |
| `--version`, `-v` | Show version |

### Convert Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o`, `--output` | `{input}.mp4` | Output file path |
| `-q`, `--quality` | `23` | CRF value (18-35, lower=better) |
| `-p`, `--preset` | `medium` | Encoding speed preset |
| `-a`, `--audio` | `192k` | Audio bitrate |
| `-r`, `--resolution` | original | Scale to resolution |
| `--no-audio` | false | Strip audio track |

### Compress Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o`, `--output` | `{input}_compressed` | Output file path |
| `-l`, `--level` | `medium` | light/medium/heavy/extreme |

---

## Tips

1. **Forgot a command?** Just run `proteus` or `proteus --help`
2. **Forgot command options?** Run `proteus convert --help`
3. **Want the docs?** Run `proteus docs`
4. **CRF sweet spot:** 23-26 for most uses, 28 for sharing

---

## Why "Proteus"?

In Greek mythology, Proteus was the "Old Man of the Sea" — a prophetic sea god who could change his shape at will. The word *protean* literally means "versatile" or "capable of assuming many forms."

Perfect for a tool that transforms videos between formats. 🔱

---

## Under the Hood

Proteus uses `ffmpeg` with sensible defaults:
- **Video:** H.264 (libx264) — universal compatibility
- **Audio:** AAC — high quality, small size
- **Container:** MP4 — plays everywhere

---

## Reinstall / Update

If you've made changes to the code, reinstall with:

```bash
cd /path/to/proteus
uv tool install . --reinstall
```

---

## Uninstall

```bash
uv tool uninstall proteus
```
