"""
Homvyx Video Builder v2
Creates faceless short-form videos using FFmpeg + Edge TTS + Product Images.
Output: 9:16 vertical videos (1080x1920) for Shorts/Reels/TikTok

Pipeline:
1. Download/generate product images
2. Generate voiceover with Edge TTS
3. Assemble video with FFmpeg (images + zoom/pan + text + audio)
"""

import asyncio
import json
import os
import sys
import subprocess
import textwrap
import urllib.request
import hashlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import TTS, VIDEO, VIDEOS_DIR, AUDIO_DIR, IMAGES_DIR


# ============================================================
# FFMPEG AUTO-DETECTION (Windows)
# ============================================================

def _find_ffmpeg():
    """Auto-detect FFmpeg location on Windows and add to PATH."""
    import shutil
    if shutil.which("ffmpeg"):
        return

    env_user = ""
    try:
        env_user = os.popen(
            'powershell -Command "[Environment]::GetEnvironmentVariable(\'Path\',\'User\')"'
        ).read().strip()
    except Exception:
        pass

    search_dirs = []

    # WinGet packages
    winget_base = os.path.join(
        os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages"
    )
    if os.path.isdir(winget_base):
        for d in os.listdir(winget_base):
            if "ffmpeg" in d.lower():
                pkg_dir = os.path.join(winget_base, d)
                for root, dirs, files in os.walk(pkg_dir):
                    if "ffmpeg.exe" in files:
                        search_dirs.append(root)
                        break

    # User PATH entries
    if env_user:
        for p in env_user.split(";"):
            if "ffmpeg" in p.lower() and os.path.isdir(p):
                search_dirs.append(p)

    # Common locations
    for d in [r"C:\ffmpeg\bin", r"C:\tools\ffmpeg\bin", r"C:\ProgramData\chocolatey\bin"]:
        if os.path.isdir(d):
            search_dirs.append(d)

    for d in search_dirs:
        if os.path.isfile(os.path.join(d, "ffmpeg.exe")):
            os.environ["PATH"] = d + ";" + os.environ.get("PATH", "")
            print(f"  [ffmpeg] Found: {d}")
            return

    print("  [ffmpeg] WARNING: Not found. Install with: winget install Gyan.FFmpeg")

_find_ffmpeg()


# ============================================================
# PRODUCT IMAGE MANAGEMENT
# ============================================================

# Free stock image URLs for generic product categories (fallback)
CATEGORY_IMAGES = {
    "kitchen gadgets": [
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=1080&h=1920&fit=crop",
    ],
    "kitchen organization": [
        "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=1080&h=1920&fit=crop",
    ],
    "home organization": [
        "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1080&h=1920&fit=crop",
    ],
    "cleaning gadgets": [
        "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=1080&h=1920&fit=crop",
        "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=1080&h=1920&fit=crop",
    ],
}


def download_image(url: str, output_dir: str, filename: str = None) -> str:
    """Download an image from a URL to local disk."""
    os.makedirs(output_dir, exist_ok=True)

    if not filename:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        ext = ".jpg"
        if ".png" in url:
            ext = ".png"
        elif ".webp" in url:
            ext = ".webp"
        filename = f"img_{url_hash}{ext}"

    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return filepath  # Already downloaded

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(filepath, "wb") as f:
                f.write(response.read())
        print(f"  [img] Downloaded: {filename} ({os.path.getsize(filepath) // 1024} KB)")
        return filepath
    except Exception as e:
        print(f"  [img] Download failed: {e}")
        return ""


def get_product_images(product: dict, count: int = 3) -> list[str]:
    """Get product images — from URL list, Amazon scrape, or stock photos."""
    images = []
    product_name = product.get("name", "product")
    safe_name = "".join(c for c in product_name if c.isalnum() or c in " -_")[:30].strip()
    img_dir = os.path.join(IMAGES_DIR, safe_name.replace(" ", "_").lower())

    # 1. Check if product has image URLs
    image_urls = product.get("image_urls", [])
    if isinstance(image_urls, str):
        image_urls = [image_urls] if image_urls.startswith("http") else []

    # Filter valid URLs only
    image_urls = [u for u in image_urls if isinstance(u, str) and u.startswith("http")]

    for i, url in enumerate(image_urls[:count]):
        img = download_image(url, img_dir, f"product_{i+1}.jpg")
        if img:
            images.append(img)

    # 2. If not enough, use stock images by category
    if len(images) < count:
        category = product.get("category", "kitchen gadgets")
        stock_urls = CATEGORY_IMAGES.get(category, CATEGORY_IMAGES["kitchen gadgets"])
        for i, url in enumerate(stock_urls):
            if len(images) >= count:
                break
            img = download_image(url, img_dir, f"stock_{i+1}.jpg")
            if img:
                images.append(img)

    # 3. Ultimate fallback: generate solid color images with FFmpeg
    while len(images) < count:
        idx = len(images) + 1
        fallback_path = os.path.join(img_dir, f"fallback_{idx}.png")
        if not os.path.exists(fallback_path):
            os.makedirs(img_dir, exist_ok=True)
            colors = ["#1a1a2e", "#16213e", "#0f3460", "#533483", "#e94560"]
            color = colors[idx % len(colors)]
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-f", "lavfi", "-i",
                     f"color=c={color}:s=1080x1920:d=1",
                     "-frames:v", "1", fallback_path],
                    capture_output=True, timeout=10
                )
            except Exception:
                pass
        if os.path.exists(fallback_path):
            images.append(fallback_path)
        else:
            break

    return images


# ============================================================
# TEXT-TO-SPEECH (Edge TTS — Free, High Quality)
# ============================================================

async def generate_tts(text: str, output_path: str, voice: str = None) -> str:
    """Generate voiceover using Edge TTS (free Microsoft neural voices)."""
    try:
        import edge_tts
    except ImportError:
        print("  [tts] edge-tts not installed. Run: pip install edge-tts")
        return ""

    voice = voice or TTS["voice"]
    rate = TTS.get("rate", "+0%")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)

    size_kb = os.path.getsize(output_path) // 1024
    print(f"  [tts] Generated: {os.path.basename(output_path)} ({voice}, {size_kb} KB)")
    return output_path


def generate_tts_sync(text: str, output_path: str, voice: str = None) -> str:
    """Synchronous wrapper for TTS generation."""
    return asyncio.run(generate_tts(text, output_path, voice))


# ============================================================
# SUBTITLE GENERATION
# ============================================================

def generate_srt(script_sections: dict, output_path: str) -> str:
    """Generate SRT subtitle file from script sections."""
    srt_content = ""
    current_time = 0
    idx = 1

    for section_name, section_data in script_sections.items():
        text = section_data["text"]
        duration = section_data["duration"]

        # Split long text into chunks for readability
        words = text.split()
        chunk_size = max(4, len(words) // max(1, duration // 3))
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))

        if not chunks:
            chunks = [text]

        chunk_duration = duration / len(chunks)

        for chunk in chunks:
            start_h = int(current_time // 3600)
            start_m = int((current_time % 3600) // 60)
            start_s = int(current_time % 60)
            start_ms = int((current_time % 1) * 1000)

            end_time = current_time + chunk_duration
            end_h = int(end_time // 3600)
            end_m = int((end_time % 3600) // 60)
            end_s = int(end_time % 60)
            end_ms = int((end_time % 1) * 1000)

            srt_content += f"{idx}\n"
            srt_content += f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d} --> "
            srt_content += f"{end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}\n"
            srt_content += f"{chunk}\n\n"

            current_time = end_time
            idx += 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"  [srt] Subtitles: {os.path.basename(output_path)} ({idx-1} cues)")
    return output_path


# ============================================================
# FFMPEG VIDEO ASSEMBLY
# ============================================================

def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 30.0


def build_video(
    product_name: str,
    script_sections: dict,
    audio_path: str,
    output_path: str,
    product_images: list[str] = None,
    subtitle_path: str = None,
) -> str:
    """
    Build a professional faceless video:
    - Product images with slow zoom/pan (Ken Burns effect)
    - Dark overlay for text readability
    - Product name text at top
    - Voiceover audio synced to images

    Falls back gracefully if images or drawtext don't work.
    """
    w, h = VIDEO["width"], VIDEO["height"]
    fps = VIDEO["fps"]
    duration = get_audio_duration(audio_path)

    print(f"  [video] Building: {os.path.basename(output_path)}")
    print(f"          Duration: {duration:.1f}s | Resolution: {w}x{h}")

    # Strategy 1: Images slideshow with zoom + text overlay
    if product_images and len(product_images) > 0:
        result = _build_slideshow_video(
            product_name, product_images, audio_path, output_path, duration
        )
        if result:
            return result

    # Strategy 2: Solid background + text + audio
    result = _build_text_video(product_name, audio_path, output_path, duration)
    if result:
        return result

    # Strategy 3: Minimal — solid color + audio only
    return _build_minimal_video(audio_path, output_path, duration)


def _build_slideshow_video(
    product_name: str,
    images: list[str],
    audio_path: str,
    output_path: str,
    duration: float,
) -> str:
    """Build slideshow video from product images with Ken Burns zoom effect."""
    w, h = VIDEO["width"], VIDEO["height"]
    fps = VIDEO["fps"]

    # Calculate per-image duration
    num_images = min(len(images), 5)  # Max 5 images
    img_duration = duration / num_images

    # Build FFmpeg input and filter_complex
    inputs = []
    filter_parts = []

    for i in range(num_images):
        img_path = images[i].replace("\\", "/")
        inputs.extend(["-loop", "1", "-t", str(img_duration), "-i", img_path])

        # Scale image to fill 1080x1920, then apply slow zoom (Ken Burns)
        # zoom from 1.0 to 1.15 over the clip duration
        zoom_speed = 0.0003  # Subtle zoom
        filter_parts.append(
            f"[{i}:v]scale={w*2}:{h*2}:force_original_aspect_ratio=increase,"
            f"crop={w*2}:{h*2},"
            f"zoompan=z='min(zoom+{zoom_speed},1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={int(img_duration*fps)}:s={w}x{h}:fps={fps},"
            f"setsar=1[v{i}]"
        )

    # Concatenate all image clips
    concat_inputs = "".join(f"[v{i}]" for i in range(num_images))
    filter_parts.append(f"{concat_inputs}concat=n={num_images}:v=1:a=0[slideshow]")

    # Dark overlay for text readability
    filter_parts.append(
        f"[slideshow]colorbalance=rs=-0.1:gs=-0.1:bs=-0.05,"
        f"eq=brightness=-0.15:contrast=1.1[darkened]"
    )

    # Product name text overlay (top)
    safe_name = product_name.replace("'", "").replace(":", " -").replace("\\", "")
    filter_parts.append(
        f"[darkened]drawtext="
        f"text='{safe_name}':"
        f"fontsize=48:fontcolor=white:"
        f"x=(w-text_w)/2:y=180:"
        f"borderw=4:bordercolor=black@0.7"
        f"[final]"
    )

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[final]",
        "-map", f"{num_images}:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  [video] Slideshow created: {size_mb:.1f} MB")
            return output_path
        else:
            # Try without drawtext (fontconfig issue)
            return _build_slideshow_no_text(
                images, audio_path, output_path, duration
            )
    except Exception as e:
        print(f"  [video] Slideshow failed: {e}")
        return ""


def _build_slideshow_no_text(
    images: list[str],
    audio_path: str,
    output_path: str,
    duration: float,
) -> str:
    """Slideshow without text overlay (fontconfig fallback)."""
    w, h = VIDEO["width"], VIDEO["height"]
    fps = VIDEO["fps"]

    num_images = min(len(images), 5)
    img_duration = duration / num_images

    inputs = []
    filter_parts = []

    for i in range(num_images):
        img_path = images[i].replace("\\", "/")
        inputs.extend(["-loop", "1", "-t", str(img_duration), "-i", img_path])

        filter_parts.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},"
            f"setsar=1,"
            f"format=yuv420p[v{i}]"
        )

    concat_inputs = "".join(f"[v{i}]" for i in range(num_images))
    filter_parts.append(f"{concat_inputs}concat=n={num_images}:v=1:a=0[final]")

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[final]",
        "-map", f"{num_images}:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  [video] Slideshow (no text) created: {size_mb:.1f} MB")
            return output_path
        else:
            err = result.stderr[-300:] if result.stderr else "unknown"
            print(f"  [video] Slideshow fallback failed: {err}")
            return ""
    except Exception as e:
        print(f"  [video] Error: {e}")
        return ""


def _build_text_video(
    product_name: str,
    audio_path: str,
    output_path: str,
    duration: float,
) -> str:
    """Build video with text on dark background + audio."""
    w, h = VIDEO["width"], VIDEO["height"]
    fps = VIDEO["fps"]

    safe_name = product_name.replace("'", "").replace(":", " -").replace("\\", "")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=#0f0f23:s={w}x{h}:d={duration}:r={fps}",
        "-i", audio_path,
        "-vf", (
            f"drawtext=text='{safe_name}':"
            f"fontsize=52:fontcolor=white:"
            f"x=(w-text_w)/2:y=180:"
            f"borderw=3:bordercolor=black"
        ),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  [video] Text video created: {size_mb:.1f} MB")
            return output_path
    except Exception:
        pass

    return ""


def _build_minimal_video(audio_path: str, output_path: str, duration: float) -> str:
    """Ultimate fallback: solid color + audio, no text."""
    w, h = VIDEO["width"], VIDEO["height"]
    fps = VIDEO["fps"]

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=#0f0f23:s={w}x{h}:d={duration}:r={fps}",
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "aac",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  [video] Minimal video created: {size_mb:.1f} MB")
            return output_path
        else:
            print(f"  [video] Minimal failed: {result.stderr[-200:]}")
            return ""
    except Exception as e:
        print(f"  [video] Error: {e}")
        return ""


# ============================================================
# FULL PIPELINE: Script → Images → Audio → Video
# ============================================================

def create_content_package(
    product: dict,
    script: dict,
    output_dir: str = None,
) -> dict:
    """
    Full pipeline: takes a product + script and outputs a ready-to-post video.

    Returns:
        {
            "video_path": str,
            "audio_path": str,
            "subtitle_path": str,
            "platform": str,
            "product_name": str,
            "caption": str,
        }
    """
    output_dir = output_dir or VIDEOS_DIR
    os.makedirs(output_dir, exist_ok=True)

    product_name = product.get("name", "Product")
    platform = script.get("platform", "youtube")
    framework = script.get("framework", "hps")

    # Sanitize filename
    safe_name = "".join(c for c in product_name if c.isalnum() or c in " -_")[:40].strip()
    base_name = f"homvyx_{safe_name}_{platform}".replace(" ", "_").lower()

    audio_path = os.path.join(AUDIO_DIR, f"{base_name}.mp3")
    srt_path = os.path.join(output_dir, f"{base_name}.srt")
    video_path = os.path.join(output_dir, f"{base_name}.mp4")

    print(f"\n{'='*55}")
    print(f"  CONTENT PACKAGE: {product_name}")
    print(f"  Platform: {platform} | Framework: {framework}")
    print(f"{'='*55}")

    # Step 1: Get product images
    print("\n  --- Step 1: Images ---")
    product_images = get_product_images(product, count=3)
    print(f"  [img] Got {len(product_images)} images")

    # Step 2: Generate voiceover
    print("\n  --- Step 2: TTS Audio ---")
    full_script = script.get("full_script", "")
    if not full_script:
        sections = script.get("sections", {})
        full_script = " ".join([s["text"] for s in sections.values()])

    generate_tts_sync(full_script, audio_path)

    if not os.path.exists(audio_path):
        print("  [FAIL] TTS failed")
        return {}

    # Step 3: Generate subtitles
    print("\n  --- Step 3: Subtitles ---")
    sections = script.get("sections", {})
    if sections:
        generate_srt(sections, srt_path)

    # Step 4: Build video
    print("\n  --- Step 4: Video Assembly ---")
    video = build_video(
        product_name=product_name,
        script_sections=sections,
        audio_path=audio_path,
        output_path=video_path,
        product_images=product_images,
        subtitle_path=srt_path if os.path.exists(srt_path) else None,
    )

    status = "ready" if video else "failed"
    print(f"\n  {'[OK]' if video else '[FAIL]'} Package {status}: {platform}")

    return {
        "video_path": video,
        "audio_path": audio_path,
        "subtitle_path": srt_path if os.path.exists(srt_path) else "",
        "platform": platform,
        "product_name": product_name,
        "caption": script.get("caption", ""),
        "description": script.get("description", ""),
        "images": product_images,
        "status": status,
    }


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":
    from content.script_generator import generate_all_scripts
    from discovery.product_finder import SEED_PRODUCTS

    product = SEED_PRODUCTS[0]

    print(f"\n{'='*60}")
    print(f"  HOMVYX VIDEO BUILDER v2 — Test Run")
    print(f"  Product: {product['name']}")
    print(f"{'='*60}")

    scripts = generate_all_scripts(product)
    yt_script = scripts[0]
    result = create_content_package(product, yt_script)

    if result.get("video_path"):
        print(f"\n{'='*60}")
        print(f"  SUCCESS!")
        print(f"  Video: {result['video_path']}")
        print(f"  Audio: {result['audio_path']}")
        print(f"  Images: {len(result.get('images', []))}")
        print(f"  Caption: {result['caption'][:100]}...")
        print(f"{'='*60}")
    else:
        print(f"\n  Video creation failed")
