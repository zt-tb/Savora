from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SEND_LIMIT = 49 * 1024 * 1024
PART_TARGET = 45 * 1024 * 1024
COMPRESS_MAX = 150 * 1024 * 1024
_CHUNK = 8 * 1024 * 1024


@dataclass
class OutFile:
    path: str
    kind: str
    part: tuple[int, int] | None = None


def _probe_duration(path: str) -> float | None:
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30)
        if probe.returncode == 0 and probe.stdout.strip():
            return float(probe.stdout.strip())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


def _compress_blocking(input_path: str, output_path: str, target_size_mb: int) -> bool:
    try:
        duration = _probe_duration(input_path) or 60.0
        target_bitrate = max(500, min(int((target_size_mb * 8192) / max(duration, 1)), 5000))
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
             "-maxrate", f"{target_bitrate}k", "-bufsize", f"{target_bitrate * 2}k",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", output_path],
            capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            logger.warning("ffmpeg ضغط فشل: %s", result.stderr[-400:])
            return False
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except subprocess.TimeoutExpired:
        logger.warning("انتهت مهلة ضغط الفيديو")
        return False
    except OSError:
        logger.warning("ffmpeg غير متوفر — تخطّي الضغط")
        return False
    except Exception:
        logger.exception("خطأ غير متوقع بالضغط")
        return False


def _split_video_blocking(path: str, part_target: int, limit: int) -> list[str] | None:
    size = os.path.getsize(path)
    duration = _probe_duration(path)
    if not duration or duration <= 0:
        return None
    root, ext = os.path.splitext(path)
    ext = ext or ".mp4"
    segment_seconds = max(2, int(duration * part_target / size))
    pattern = f"{root}_part%03d{ext}"
    cmd = ["ffmpeg", "-y", "-i", path, "-map", "0:v:0", "-map", "0:a?", "-c", "copy", "-sn", "-dn",
           "-f", "segment", "-segment_time", str(segment_seconds), "-reset_timestamps", "1"]
    if ext.lower() in (".mp4", ".m4v", ".mov"):
        cmd += ["-segment_format_options", "movflags=+faststart"]
    cmd.append(pattern)
    created: list[str] = []
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        folder, prefix = os.path.split(root)
        created = sorted(
            os.path.join(folder, n) for n in os.listdir(folder or ".")
            if n.startswith(prefix + "_part") and n.endswith(ext))
        if result.returncode != 0 or not created:
            logger.warning("ffmpeg تقطيع فشل: %s", result.stderr[-400:])
            raise RuntimeError("segment failed")
        if any(os.path.getsize(p) > limit or os.path.getsize(p) == 0 for p in created):
            raise RuntimeError("segment too large")
        return created
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        for p in created:
            try:
                os.remove(p)
            except OSError:
                pass
        return None


def _split_bytes_blocking(path: str, part_target: int) -> list[str]:
    parts: list[str] = []
    index = 1
    with open(path, "rb") as src:
        while True:
            part_path = f"{path}.part{index:03d}"
            written = 0
            with open(part_path, "wb") as dst:
                while written < part_target:
                    chunk = src.read(min(_CHUNK, part_target - written))
                    if not chunk:
                        break
                    dst.write(chunk)
                    written += len(chunk)
            if written == 0:
                os.remove(part_path)
                break
            parts.append(part_path)
            index += 1
    return parts


def _remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


async def prepare_for_send(path: str, kind: str, *, limit: int = SEND_LIMIT, part_target: int = PART_TARGET,
                           compress_max: int = COMPRESS_MAX) -> list[OutFile]:
    size = os.path.getsize(path)
    if size <= limit:
        return [OutFile(path, kind)]

    if kind == "video":
        if size <= compress_max:
            out = path + ".compressed.mp4"
            ok = await asyncio.to_thread(_compress_blocking, path, out, max(1, part_target // (1024 * 1024)))
            if ok and os.path.getsize(out) <= limit:
                _remove(path)
                return [OutFile(out, "video")]
            _remove(out)
        parts = await asyncio.to_thread(_split_video_blocking, path, part_target, limit)
        if parts:
            _remove(path)
            return [OutFile(p, "video", (i, len(parts))) for i, p in enumerate(parts, 1)]

    parts = await asyncio.to_thread(_split_bytes_blocking, path, part_target)
    _remove(path)
    return [OutFile(p, "document", (i, len(parts))) for i, p in enumerate(parts, 1)]
