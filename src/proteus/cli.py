"""
Proteus CLI — Transform your videos with ease.

Named after the Greek god who could change into any shape.
"""

import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="proteus",
    help="🔱 Proteus — Shape-shifting video converter. Transform formats and compress with ease.",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


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
) -> None:
    """
    Convert video to MP4 (H.264).
    
    [bold green]Examples:[/]
    
      [dim]# Simple conversion with smart defaults[/]
      proteus convert video.mov
      
      [dim]# Specify output name[/]
      proteus convert video.mov -o converted.mp4
      
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

    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(input_file),
        "-c:v", "libx264",
        "-crf", str(quality),
        "-preset", preset,
    ]

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

    rprint(Panel(
        f"[bold]Converting:[/] {input_file.name}\n"
        f"[bold]Output:[/] {output.name}\n"
        f"[bold]Quality:[/] CRF {quality} ({preset})",
        title="🔱 Proteus",
        border_style="blue",
    ))

    try:
        subprocess.run(cmd, check=True)
        
        # Show file size comparison
        input_size = input_file.stat().st_size / (1024 * 1024)
        output_size = output.stat().st_size / (1024 * 1024)
        ratio = (output_size / input_size) * 100 if input_size > 0 else 0
        
        rprint(f"\n[bold green]✓ Done![/]")
        rprint(f"  Input:  {input_size:.1f} MB")
        rprint(f"  Output: {output_size:.1f} MB ({ratio:.0f}% of original)")
        rprint(f"  Saved:  [cyan]{output}[/]")
        
    except subprocess.CalledProcessError as e:
        rprint(f"[bold red]Error:[/] ffmpeg failed with code {e.returncode}")
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
) -> None:
    """
    Smart compression with presets.
    
    [bold green]Examples:[/]
    
      [dim]# Medium compression (good balance)[/]
      proteus compress video.mp4
      
      [dim]# Heavy compression for sharing[/]
      proteus compress video.mp4 -l heavy
      
      [dim]# Extreme compression (noticeable quality loss)[/]
      proteus compress video.mp4 -l extreme
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
    
    rprint(f"[dim]Using {level} compression (CRF {crf})...[/]\n")
    
    # Delegate to convert
    convert(
        input_file=input_file,
        output=output,
        quality=crf,
        preset=preset,
        audio_bitrate=audio,
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
        typer.Option("--version", "-v", help="Show version"),
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
