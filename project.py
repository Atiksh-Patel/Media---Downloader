import argparse
import shutil
import sys
from pathlib import Path
 
try:
    import yt_dlp
except ImportError:
    sys.exit("yt-dlp is not installed. Run: pip install -U yt-dlp")
 
QUALITIES = ["best", "2160", "1440", "1080", "720", "480", "360", "audio"]
 
 
def build_format(quality: str) -> str:
    """Return a yt-dlp format selector for the chosen quality."""
    if quality == "audio":
        return "bestaudio/best"
    if quality == "best":
        return "bestvideo+bestaudio/best"
    # Best video up to the chosen height, falling back gracefully
    return (
        f"bestvideo[height<={quality}]+bestaudio/"
        f"best[height<={quality}]/best"
    )
 
 
def progress_hook(d: dict) -> None:
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        print(f"\r  {percent} | {speed} | ETA {eta}   ", end="", flush=True)
    elif d["status"] == "finished":
        print("\n  Download finished, processing...")
 
 
def download(url: str, quality: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    has_ffmpeg = shutil.which("ffmpeg") is not None
 
    if not has_ffmpeg:
        print("Warning: FFmpeg not found. Falling back to a single-file "
              "format (quality may be limited, no MP3 conversion).")
 
    opts = {
        "format": build_format(quality) if has_ffmpeg
                  else (f"best[height<={quality}]/best" if quality.isdigit()
                        else "best"),
        "outtmpl": str(out_dir / "%(title)s [%(id)s].%(ext)s"),
        "noplaylist": True,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": False,
        "windowsfilenames": sys.platform.startswith("win"),
    }
 
    if has_ffmpeg:
        if quality == "audio":
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        else:
            opts["merge_output_format"] = "mp4"
 
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print(f"Title:    {info.get('title')}")
        print(f"Channel:  {info.get('uploader')}")
        print(f"Duration: {info.get('duration_string', 'unknown')}")
        print(f"Quality:  {quality}")
        print(f"Saving to: {out_dir}\n")
        ydl.download([url])
 
    print(f"\nDone! Saved in: {out_dir}")
 
 
def ask_quality() -> str:
    print("\nChoose quality:")
    for i, q in enumerate(QUALITIES, 1):
        label = {"best": "Best available", "audio": "Audio only (MP3)"}.get(
            q, f"{q}p")
        print(f"  {i}. {label}")
    while True:
        choice = input(f"Enter number [1-{len(QUALITIES)}] (default 1): ").strip()
        if not choice:
            return QUALITIES[0]
        if choice.isdigit() and 1 <= int(choice) <= len(QUALITIES):
            return QUALITIES[int(choice) - 1]
        print("Invalid choice, try again.")
 
 
def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube video downloader")
    parser.add_argument("url", nargs="?", help="YouTube video URL")
    parser.add_argument("-q", "--quality", choices=QUALITIES,
                        help="Video quality (default: ask interactively)")
    parser.add_argument("-o", "--output", type=Path,
                        default=Path.home() / "Downloads",
                        help="Output folder (default: ~/Downloads)")
    args = parser.parse_args()
 
    url = args.url or input("Enter YouTube URL: ").strip()
    if not url:
        sys.exit("No URL provided.")
    quality = args.quality or ask_quality()
 
    try:
        download(url, quality, args.output.expanduser())
    except yt_dlp.utils.DownloadError as e:
        sys.exit(f"\nDownload failed: {e}")
    except KeyboardInterrupt:
        sys.exit("\nCancelled by user.")
 
 
if __name__ == "__main__":
    main()