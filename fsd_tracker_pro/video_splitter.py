import os
import math
import subprocess
from pathlib import Path
from typing import List

def split_video_into_clips(
    video_path: str, 
    output_dir: str, 
    clip_length_minutes: int = 5
) -> List[str]:
    """
    Splits a local video into N chunks each of `clip_length_minutes`.
    Returns a list of paths to the generated clips.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # One way to get video duration (in seconds) using ffprobe:
    cmd_duration = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd_duration, capture_output=True, text=True)
    duration_seconds = float(result.stdout.strip())
    clip_length_seconds = clip_length_minutes * 60
    num_clips = math.ceil(duration_seconds / clip_length_seconds)

    clip_paths = []

    for i in range(num_clips):
        start_time = i * clip_length_seconds
        clip_output = os.path.join(output_dir, f"clip_{i+1}.mp4")

        # ffmpeg to extract the subclip
        cmd_extract = [
            "ffmpeg",
            "-y",  # overwrite
            "-i", video_path,
            "-ss", str(start_time),
            "-t", str(clip_length_seconds),
            "-c", "copy",
            clip_output
        ]
        subprocess.run(cmd_extract, capture_output=True, text=True)
        clip_paths.append(clip_output)

    return clip_paths