"""
Proteus CLI — Transform your videos with ease.

Named after the Greek god who could change into any shape.
"""

import random
import re
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

app = typer.Typer(
    name="proteus",
    help="🔱 Proteus — Shape-shifting video converter. Transform formats and compress with ease.",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()

# Tips shown during encoding - instructional hints with commands
TIPS = [
    "Tip: Use [cyan]proteus compress video.mp4 -l heavy[/] for smaller files",
    "Tip: Use [cyan]proteus compress video.mp4 -l extreme[/] for max compression",
    "Tip: Use [cyan]proteus convert video.mov -r 720[/] to scale to 720p",
    "Tip: Use [cyan]proteus convert video.mov --no-audio[/] to remove audio",
    "Tip: Use [cyan]proteus sizes video.mp4[/] to preview all compression options",
    "Tip: Use [cyan]proteus info video.mp4[/] to inspect codec & resolution",
    "Tip: Use [cyan]proteus docs[/] to view full documentation",
]


def get_package_dir() -> Path:
    """Get the package installation directory."""
    return Path(__file__).parent.parent.parent


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_video_duration(path: Path) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        import json
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0))
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return 0


def estimate_output_size(input_size_mb: float, crf: int, resolution_scale: float = 1.0) -> float:
    """
    Estimate output size based on CRF value.
    
    This is a rough approximation — actual results vary by content.
    CRF compression ratios (approximate):
      18: 60-70% of original
      23: 35-45% of original  
      28: 18-25% of original
      35: 8-12% of original
    """
    # Rough multipliers for different CRF values
    crf_multipliers = {
        18: 0.65,
        19: 0.58,
        20: 0.50,
        21: 0.45,
        22: 0.40,
        23: 0.35,
        24: 0.30,
        25: 0.27,
        26: 0.24,
        27: 0.21,
        28: 0.18,
        29: 0.16,
        30: 0.14,
        31: 0.12,
        32: 0.11,
        33: 0.10,
        34: 0.09,
        35: 0.08,
    }
    
    # Clamp CRF and get multiplier
    crf_clamped = max(18, min(35, crf))
    multiplier = crf_multipliers.get(crf_clamped, 0.35)
    
    # Resolution scaling affects size roughly quadratically
    estimated = input_size_mb * multiplier * (resolution_scale ** 2)
    
    return estimated


def format_size(size_mb: float) -> str:
    """Format size in MB or GB as appropriate."""
    if size_mb >= 1000:
        return f"{size_mb / 1024:.1f} GB"
    return f"{size_mb:.1f} MB"


def get_video_info(path: Path) -> dict:
    """Get video information using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        import json
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}


def parse_ffmpeg_time(time_str: str) -> float:
    """Parse ffmpeg time string (HH:MM:SS.ms) to seconds."""
    match = re.match(r'(\d+):(\d+):(\d+\.?\d*)', time_str)
    if match:
        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)
    return 0


def run_ffmpeg_with_progress(cmd: list, duration: float, verbose: bool = False) -> bool:
    """Run ffmpeg with a progress bar, optionally showing verbose output."""
    if verbose:
        # Verbose mode: just run ffmpeg normally
        result = subprocess.run(cmd)
        return result.returncode == 0
    
    # Show a random tip before starting
    tip = random.choice(TIPS)
    rprint(f"[dim]{tip}[/]")
    
    # Add progress flag for parsing
    cmd_with_progress = cmd[:-2] + ["-progress", "pipe:1", "-nostats"] + cmd[-2:]
    
    # Use context manager for proper cleanup
    with subprocess.Popen(
        cmd_with_progress,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        with Progress(
            SpinnerColumn(),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Converting", total=100)
            
            current_time = 0
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                # Parse progress output
                if line.startswith("out_time="):
                    time_str = line.split("=")[1].strip()
                    current_time = parse_ffmpeg_time(time_str)
                    if duration > 0:
                        percent = min(100, (current_time / duration) * 100)
                        progress.update(task, completed=percent)
                elif line.startswith("progress=end"):
                    progress.update(task, completed=100)
        
        return process.returncode == 0


@app.command()
def convert(
    input_file: Annotated[Path, typer.Argument(help="Input video file (e.g., video.mov)")],
    output: Annotated[
        Optional[Path],
        typer.Option("-o", "--output", help="Output file path. Defaults to input name with .mp4"),
    ] = None,
    quality: Annotated[
        int,
        typer.Option("-q", "--quality", help="Quality (CRF): 18=high, 23=medium, 28=low/small. Lower=better quality, bigger file"),
    ] = 23,
    preset: Annotated[
        str,
        typer.Option("-p", "--preset", help="Encoding speed: ultrafast, fast, medium, slow, veryslow"),
    ] = "medium",
    audio_bitrate: Annotated[
        str,
        typer.Option("-a", "--audio", help="Audio bitrate (e.g., 128k, 192k, 320k)"),
    ] = "192k",
    resolution: Annotated[
        Optional[str],
        typer.Option("-r", "--resolution", help="Scale to resolution (e.g., 1920x1080, 1280x720, or just height like 720)"),
    ] = None,
    no_audio: Annotated[
        bool,
        typer.Option("--no-audio", help="Remove audio track"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-V", help="Show full ffmpeg output"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite output file if it exists"),
    ] = False,
    slow: Annotated[
        bool,
        typer.Option("--slow", help="Use software encoding (slower but ~20%% smaller files)"),
    ] = False,
) -> None:
    """
    Convert video to MP4 (H.264).
    
    [bold green]Examples:[/]
    
      [dim]# Fast conversion (hardware accelerated)[/]
      proteus convert video.mov
      
      [dim]# Best compression (slower)[/]
      proteus convert video.mov --slow
      
      [dim]# Lower quality for smaller file[/]
      proteus convert video.mov -q 28
      
      [dim]# Scale down to 720p[/]
      proteus convert video.mov -r 720
    """
    if not check_ffmpeg():
        rprint("[bold red]Error:[/] ffmpeg not found. Install with: [cyan]brew install ffmpeg[/]")
        raise typer.Exit(1)

    if not input_file.exists():
        rprint(f"[bold red]Error:[/] File not found: {input_file}")
        raise typer.Exit(1)

    # Default output: same name, .mp4 extension
    if output is None:
        output = input_file.with_suffix(".mp4")
        if output == input_file:
            output = input_file.with_stem(f"{input_file.stem}_converted").with_suffix(".mp4")

    # Check if output already exists
    if output.exists() and not force:
        rprint(f"[bold yellow]Warning:[/] Output file already exists: [cyan]{output}[/]")
        rprint(f"  Use [cyan]--force[/] or [cyan]-f[/] to overwrite")
        raise typer.Exit(1)

    # Get duration for progress bar
    duration = get_video_duration(input_file)
    
    # Get input size and estimate output
    input_size = input_file.stat().st_size / (1024 * 1024)
    
    # Get video info for resolution detection
    info = get_video_info(input_file)
    orig_width, orig_height = 1920, 1080  # defaults
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            orig_width = stream.get("width", 1920)
            orig_height = stream.get("height", 1080)
            break
    
    # Calculate resolution scale factor if scaling down
    resolution_scale = 1.0
    if resolution:
        if "x" in resolution:
            target_height = int(resolution.split("x")[1])
        else:
            target_height = int(resolution)
        resolution_scale = target_height / orig_height
    
    estimated_size = estimate_output_size(input_size, quality, resolution_scale)
    
    # Build resolution hint for large videos
    resolution_hint = None
    if orig_height > 1080 and not resolution:
        # Suggest scaling down - reconstruct the command with -r 1080
        suggested_res = 1080
        cmd_parts = ["proteus"]
        # Detect if we're in compress or convert mode based on output name
        if "_compressed" in str(output):
            cmd_parts.append("compress")
            cmd_parts.append(f"'{input_file}'")
            # Map CRF back to level for compress command
            crf_to_level = {20: "light", 26: "medium", 30: "heavy", 35: "extreme"}
            level_name = crf_to_level.get(quality, None)
            if level_name and level_name != "medium":
                cmd_parts.append(f"-l {level_name}")
        else:
            cmd_parts.append("convert")
            cmd_parts.append(f"'{input_file}'")
            if quality != 23:
                cmd_parts.append(f"-q {quality}")
        cmd_parts.append(f"-r {suggested_res}")
        if force:
            cmd_parts.append("-f")
        if slow:
            cmd_parts.append("--slow")
        suggested_cmd = " ".join(cmd_parts)
        resolution_hint = f"[dim]📐 Video is {orig_width}x{orig_height}. Scale down for faster encoding + smaller file:[/]\n   [cyan]{suggested_cmd}[/]"

    # Build ffmpeg command
    if slow:
        # Software encoding (slower but better compression)
        cmd = ["ffmpeg", "-i", str(input_file)]
        cmd.extend(["-c:v", "libx264", "-crf", str(quality), "-preset", preset])
        encoder_label = f"CRF {quality}, slow"
        hint = "[dim]⚡ Omit --slow for 5-10x faster encoding[/]"
    else:
        # Hardware acceleration (VideoToolbox on macOS) - DEFAULT
        # Use hardware decoding AND encoding for maximum speed
        cmd = ["ffmpeg", "-hwaccel", "videotoolbox", "-i", str(input_file)]
        # Map CRF roughly to VideoToolbox quality (0-100, lower=better)
        # CRF 18 -> q 30, CRF 23 -> q 50, CRF 28 -> q 65, CRF 35 -> q 80
        vt_quality = min(100, max(0, int(20 + (quality - 18) * 3.5)))
        cmd.extend(["-c:v", "h264_videotoolbox", "-q:v", str(vt_quality)])
        encoder_label = "⚡ hardware"
        hint = "[dim]📦 Add --slow for ~20% smaller files (5-10x slower)[/]"

    # Handle audio
    if no_audio:
        cmd.extend(["-an"])
    else:
        cmd.extend(["-c:a", "aac", "-b:a", audio_bitrate])

    # Handle resolution scaling
    if resolution:
        if "x" in resolution:
            scale = resolution
        else:
            # Just height provided, maintain aspect ratio
            scale = f"-2:{resolution}"
        cmd.extend(["-vf", f"scale={scale}"])

    # Output file (overwrite if exists)
    cmd.extend(["-y", str(output)])

    rprint(f"🔱 [bold]{input_file.name}[/] → [cyan]{output.name}[/]")
    rprint(f"   {format_size(input_size)} → ~{format_size(estimated_size)} estimated  [dim]({encoder_label})[/]")
    rprint(hint)
    if resolution_hint:
        rprint(resolution_hint)

    success = run_ffmpeg_with_progress(cmd, duration, verbose)
    
    if success:
        # Show file size comparison
        output_size = output.stat().st_size / (1024 * 1024)
        
        # Calculate compression stats
        if input_size > 0:
            ratio = output_size / input_size
            saved_mb = input_size - output_size
            
            if ratio < 1:
                compression_factor = 1 / ratio
                rprint(f"[bold green]✓ Done[/]  {format_size(input_size)} → {format_size(output_size)}  [cyan]{compression_factor:.1f}x smaller[/]  [dim](saved {format_size(saved_mb)})[/]")
            else:
                rprint(f"[bold green]✓ Done[/]  {format_size(input_size)} → {format_size(output_size)}")
        else:
            rprint(f"[bold green]✓ Done[/]  → {format_size(output_size)}")
        
        # Suggest further compression options
        further_hints = []
        is_compress_cmd = "_compressed" in str(output)
        
        # Suggest --slow if not already using it
        if not slow:
            further_hints.append("--slow")
        
        # Suggest lower resolution
        current_res = int(resolution) if resolution and resolution.isdigit() else orig_height
        if current_res > 720:
            further_hints.append("-r 720")
        elif current_res > 480:
            further_hints.append("-r 480")
        
        # Suggest heavier compression level (only for compress command)
        if is_compress_cmd:
            crf_to_level = {20: "light", 26: "medium", 30: "heavy", 35: "extreme"}
            current_level = crf_to_level.get(quality, "medium")
            level_order = ["light", "medium", "heavy", "extreme"]
            if current_level in level_order:
                idx = level_order.index(current_level)
                if idx < len(level_order) - 1:
                    next_level = level_order[idx + 1]
                    further_hints.append(f"-l {next_level}")
        
        if further_hints:
            # Build the suggested command
            cmd_parts = ["proteus"]
            if is_compress_cmd:
                cmd_parts.append("compress")
                cmd_parts.append(f"'{input_file}'")
            else:
                cmd_parts.append("convert")
                cmd_parts.append(f"'{input_file}'")
            cmd_parts.extend(further_hints)
            cmd_parts.append("-f")
            suggested_cmd = " ".join(cmd_parts)
            rprint(f"[dim]📉 Compress further: [cyan]{suggested_cmd}[/][/]")
    else:
        rprint(f"[bold red]✗ Failed[/] — run with [cyan]--verbose[/] to see details")
        raise typer.Exit(1)


@app.command()
def compress(
    input_file: Annotated[Path, typer.Argument(help="Input video file")],
    output: Annotated[
        Optional[Path],
        typer.Option("-o", "--output", help="Output file path"),
    ] = None,
    target_size: Annotated[
        Optional[int],
        typer.Option("-s", "--size", help="Target size in MB (approximate)"),
    ] = None,
    level: Annotated[
        str,
        typer.Option("-l", "--level", help="Compression level: light, medium, heavy, extreme"),
    ] = "medium",
    resolution: Annotated[
        Optional[str],
        typer.Option("-r", "--resolution", help="Scale to resolution (e.g., 1080, 720)"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-V", help="Show full ffmpeg output"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite output file if it exists"),
    ] = False,
    slow: Annotated[
        bool,
        typer.Option("--slow", help="Use software encoding (~20%% smaller, 5-10x slower)"),
    ] = False,
) -> None:
    """
    Smart compression with presets.
    
    [bold green]Examples:[/]
    
      [dim]# Fast compression (hardware)[/]
      proteus compress video.mp4
      
      [dim]# Scale down 4K to 1080p[/]
      proteus compress video.mp4 -r 1080
      
      [dim]# Heavy compression for sharing[/]
      proteus compress video.mp4 -l heavy
    """
    # Map levels to CRF values and presets
    levels = {
        "light": (20, "fast", "128k"),
        "medium": (26, "medium", "96k"),
        "heavy": (30, "slow", "64k"),
        "extreme": (35, "slower", "48k"),
    }
    
    if level not in levels:
        rprint(f"[bold red]Error:[/] Unknown level '{level}'. Use: light, medium, heavy, extreme")
        raise typer.Exit(1)
    
    crf, preset, audio = levels[level]
    
    if output is None:
        output = input_file.with_stem(f"{input_file.stem}_compressed")
    
    # Delegate to convert
    convert(
        input_file=input_file,
        output=output,
        quality=crf,
        preset=preset,
        audio_bitrate=audio,
        resolution=resolution,
        verbose=verbose,
        force=force,
        slow=slow,
    )


@app.command()
def info(
    input_file: Annotated[Path, typer.Argument(help="Video file to inspect")],
) -> None:
    """
    Show video file information.
    
    [bold green]Example:[/]
    
      proteus info video.mov
    """
    if not input_file.exists():
        rprint(f"[bold red]Error:[/] File not found: {input_file}")
        raise typer.Exit(1)

    data = get_video_info(input_file)
    
    if not data:
        rprint("[bold red]Error:[/] Could not read video info. Is ffprobe installed?")
        raise typer.Exit(1)

    table = Table(title=f"🎬 {input_file.name}", border_style="blue")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    # File info
    fmt = data.get("format", {})
    size_mb = int(fmt.get("size", 0)) / (1024 * 1024)
    duration = float(fmt.get("duration", 0))
    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
    
    table.add_row("Size", f"{size_mb:.1f} MB")
    table.add_row("Duration", duration_str)
    table.add_row("Format", fmt.get("format_long_name", "Unknown"))

    # Stream info
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            table.add_row("Video Codec", stream.get("codec_name", "?"))
            table.add_row("Resolution", f"{stream.get('width', '?')}x{stream.get('height', '?')}")
            fps = stream.get("r_frame_rate", "0/1")
            if "/" in fps:
                num, den = fps.split("/")
                fps = round(int(num) / int(den), 2) if int(den) > 0 else 0
            table.add_row("Frame Rate", f"{fps} fps")
        elif stream.get("codec_type") == "audio":
            table.add_row("Audio Codec", stream.get("codec_name", "?"))
            table.add_row("Sample Rate", f"{stream.get('sample_rate', '?')} Hz")
            table.add_row("Channels", str(stream.get("channels", "?")))

    console.print(table)


@app.command()
def sizes(
    input_file: Annotated[Path, typer.Argument(help="Video file to analyze")],
) -> None:
    """
    Preview expected file sizes for different compression settings.
    
    Shows estimated output sizes without converting — helps you choose
    the right quality/size tradeoff before committing to a long encode.
    
    [bold green]Example:[/]
    
      proteus sizes video.mov
    """
    if not input_file.exists():
        rprint(f"[bold red]Error:[/] File not found: {input_file}")
        raise typer.Exit(1)

    input_size = input_file.stat().st_size / (1024 * 1024)
    
    rprint(f"\n🔱 [bold]{input_file.name}[/]  ({format_size(input_size)})\n")
    
    table = Table(title="Estimated Output Sizes", border_style="blue")
    table.add_column("Setting", style="cyan")
    table.add_column("CRF", style="white", justify="center")
    table.add_column("Est. Size", style="white", justify="right")
    table.add_column("Reduction", style="green", justify="right")
    table.add_column("Command", style="dim")
    
    # Different quality presets to show
    presets = [
        ("High quality", 18, "proteus convert {f} -q 18"),
        ("Good quality (default)", 23, "proteus convert {f}"),
        ("Smaller file", 28, "proteus convert {f} -q 28"),
        ("compress -l light", 20, "proteus compress {f} -l light"),
        ("compress -l medium", 26, "proteus compress {f}"),
        ("compress -l heavy", 30, "proteus compress {f} -l heavy"),
        ("compress -l extreme", 35, "proteus compress {f} -l extreme"),
    ]
    
    for name, crf, cmd in presets:
        est_size = estimate_output_size(input_size, crf)
        reduction = ((input_size - est_size) / input_size) * 100 if input_size > 0 else 0
        
        # Format command with short filename
        short_name = input_file.name if len(input_file.name) < 20 else "video.mp4"
        cmd_formatted = cmd.format(f=short_name)
        
        table.add_row(
            name,
            str(crf),
            format_size(est_size),
            f"-{reduction:.0f}%",
            cmd_formatted,
        )
    
    console.print(table)
    rprint("\n[dim]Note: Estimates are approximate. Actual sizes vary by video content.[/]\n")


@app.command()
def docs() -> None:
    """
    Show documentation (renders README in terminal).
    
    Opens the Proteus documentation right in your terminal with beautiful formatting.
    """
    readme_path = get_package_dir() / "README.md"
    
    if not readme_path.exists():
        # Try alternate locations
        alt_paths = [
            Path(__file__).parent.parent.parent / "README.md",
            Path(__file__).parent.parent.parent.parent / "README.md",
        ]
        for alt in alt_paths:
            if alt.exists():
                readme_path = alt
                break
    
    if not readme_path.exists():
        rprint("[bold yellow]README not found locally.[/]")
        rprint("\nQuick reference:\n")
        rprint("  [cyan]proteus convert video.mov[/]        → Convert to MP4")
        rprint("  [cyan]proteus convert video.mov -q 28[/]  → Convert with smaller size")
        rprint("  [cyan]proteus compress video.mp4[/]       → Smart compression")
        rprint("  [cyan]proteus compress video.mp4 -l heavy[/] → Heavy compression")
        rprint("  [cyan]proteus info video.mov[/]           → Show video details")
        rprint("\nRun [cyan]proteus --help[/] or [cyan]proteus <command> --help[/] for more.")
        return

    with open(readme_path, "r") as f:
        content = f.read()
    
    md = Markdown(content)
    console.print(md)


@app.command()
def formats() -> None:
    """
    Show common format conversion examples.
    """
    rprint(Panel.fit(
        "[bold cyan]Common Conversions[/]\n\n"
        "[bold].mov → .mp4[/]\n"
        "  proteus convert video.mov\n\n"
        "[bold].avi → .mp4[/]\n"
        "  proteus convert video.avi\n\n"
        "[bold].mkv → .mp4[/]\n"
        "  proteus convert video.mkv\n\n"
        "[bold]Any → .mp4 (small)[/]\n"
        "  proteus convert video.mov -q 28\n\n"
        "[bold]Any → .mp4 (720p)[/]\n"
        "  proteus convert video.mov -r 720\n\n"
        "[bold]Remove audio[/]\n"
        "  proteus convert video.mov --no-audio",
        title="🔱 Format Cheatsheet",
        border_style="blue",
    ))


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", help="Show version"),
    ] = False,
) -> None:
    """
    🔱 Proteus — Shape-shifting video converter.
    
    Named after the Greek god who could transform into any shape.
    Uses ffmpeg under the hood for reliable, high-quality conversions.
    """
    if version:
        from proteus import __version__
        rprint(f"Proteus v{__version__}")
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        rprint(ctx.get_help())


if __name__ == "__main__":
    app()
