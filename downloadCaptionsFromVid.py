import argparse
import re
from pathlib import Path
from tempfile import TemporaryDirectory
import yt_dlp
import os

def clean_vtt(vtt_text: str) -> str:
    lines = []
    for raw_line in vtt_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "WEBVTT":
            continue
        if line.startswith("Kind:"):
            continue
        if line.startswith("Language:"):
            continue
        if "-->" in line:
            continue
        if line.isdigit():
            continue

        # Remove inline VTT cues like <00:00:01.120>
        line = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", line).strip()
        # Remove all remaining VTT/HTML-like tags (e.g. <c>, </c>, <i>, etc.)
        line = re.sub(r"<[^>]+>", "", line).strip()
        if line:
            lines.append(line)

    # Remove immediate duplicates often present in auto-captions
    deduped = []
    for line in lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return "\n".join(deduped)


def _download_single_caption_track(url: str, temp_dir: Path, lang: str) -> tuple[str, Path]:
    outtmpl = str(temp_dir / "%(id)s")
    variants = [lang, f"{lang}-US", f"{lang}-GB", "en"]

    with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    if "entries" in info:
        raise RuntimeError("Playlist URL detected. Please use a single video URL.")

    video_id = info.get("id")
    manual = info.get("subtitles", {}) or {}
    auto = info.get("automatic_captions", {}) or {}

    have_manual = any(k in manual for k in variants)
    have_auto = any(k in auto for k in variants)

    if not have_manual and not have_auto:
        raise RuntimeError("No subtitles found for this video in the requested language.")

    mode = (
        {"writesubtitles": True, "writeautomaticsub": False}
        if have_manual
        else {"writesubtitles": False, "writeautomaticsub": True}
    )

    ydl_opts = {
        "skip_download": True,
        "subtitleslangs": variants,
        "subtitlesformat": "vtt",
        "outtmpl": outtmpl,
        "noplaylist": True,
        **mode,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    candidates = sorted(temp_dir.glob(f"{video_id}*.vtt"))
    if not candidates:
        raise RuntimeError("Subtitle file was not downloaded correctly.")

    best = max(candidates, key=lambda p: p.stat().st_size)
    return video_id, best


def download_transcript(url: str, out_dir: Path, lang: str = "en") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="yt_subs_") as temp_root:
        temp_dir = Path(temp_root)
        video_id, vtt_path = _download_single_caption_track(url, temp_dir, lang)
        transcript_text = clean_vtt(vtt_path.read_text(encoding="utf-8", errors="ignore"))
    
    item_cnt = len(os.listdir(out_dir))    
    if "BhagavadGita" in str(out_dir):
        transcript_path = out_dir / f"BG{item_cnt+1}.txt"

    if "Upanishad" in str(out_dir):
        transcript_path = out_dir / f"UP{item_cnt+1}.txt"

    transcript_path.write_text(transcript_text, encoding="utf-8")
    return transcript_path

def main() -> None:
    parser = argparse.ArgumentParser(description="Download YouTube transcript from a URL.")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument(
        "--out-dir",
        default="transcripts",
        help="Directory to save subtitle and transcript files",
    )
    parser.add_argument("--lang", default="en", help="Subtitle language code (default: en)")
    args = parser.parse_args()

    transcript_path = download_transcript(args.url, Path(args.out_dir), args.lang)
    print(f"Transcript saved to: {transcript_path}")

if __name__ == "__main__":
    main()