import os
import math
import time
import requests
import asyncio
import subprocess
import tempfile
from typing import Optional
from google import genai
from google.genai import types
from tqdm import tqdm
from fsd_tracker_pro.response_model import Analysis

class VideoAnalyzer:
    def __init__(self, api_key: Optional[str] = None,  config: dict = None):
        # Fallback to environment variable if no explicit key is passed
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Make sure it's set in your .env or environment.")
        self.client = genai.Client(api_key=self.api_key)
        self.config = config or {}
        self.clip_length_minutes = self.config.get("clip_length_minutes", 3)
        self.max_concurrency = self.config.get("max_concurrency", 3)
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.retry_wait = 5

    def _retry_on_connection_reset(self, func):
        while True:
            try:
                return func()
            except requests.exceptions.ConnectionError as e:
                if "Connection reset by peer" in str(e):
                    time.sleep(self.retry_wait)
                    continue
    
    async def _retry_on_connection_reset_async(self, func):
        while True:
            try:
                return await func()
            except requests.exceptions.ConnectionError as e:
                if "Connection reset by peer" in str(e):
                    await asyncio.sleep(self.retry_wait)
                    continue

    def analyze_clip(self, clip_path: str, prompt: str) -> list[Analysis]:
        """
        Analyzes a video clip using the google-genai client.

        Configures the google-genai client with the API key, then generates
        text using the given prompt (augmented with clip information).
        """
        # Upload the video clip file.
        uploaded_file = self._retry_on_connection_reset(lambda: self.client.files.upload(file=clip_path))
        while uploaded_file.state != "ACTIVE":
            time.sleep(self.retry_wait)
            uploaded_file = self._retry_on_connection_reset(lambda: self.client.files.get(name=uploaded_file.name))
        # wait until the file is ready
        file_uri = uploaded_file.uri  # Get the URI from the file object
        mime_type = uploaded_file.mime_type  # Get the mime_type from the file object

        # Generate content using the uploaded file and the given prompt.
        model = self.config.get("model", "gemini-2.0-flash")
       
        response = self._retry_on_connection_reset(lambda: self.client.models.generate_content(
            model=model,
            contents=[
            types.Part.from_text(text=prompt), 
            types.Part.from_uri(file_uri=file_uri, mime_type=mime_type)
        ],
        config={
            'response_mime_type': 'application/json',
            'response_schema': list[Analysis],
            'temperature': 0.0
            },
        ))
        # finished, delete the file
        self._retry_on_connection_reset(lambda: self.client.files.delete(name=uploaded_file.name))
        return response.parsed if response and hasattr(response, "parsed") else []
    
    def _get_video_duration(self, video_path: str) -> int:
        # Get video duration in seconds using ffprobe.
        cmd_duration = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(cmd_duration, capture_output=True, text=True)
        duration_seconds = float(result.stdout.strip())
        return duration_seconds
    
    def _split_video_into_clips(self, video_path: str, duration_seconds: int, clip_length_minutes: int) -> list:
        """
        Splits the video into clips of given length.
        Returns a list of clip file paths.
        """
        tmp_dir = tempfile.mkdtemp(prefix="video_clips_")
        clip_length_seconds = clip_length_minutes * 60
        num_clips = math.ceil(duration_seconds / clip_length_seconds)

        clip_paths = []
        for i in range(num_clips):
            start_time = i * clip_length_seconds
            clip_output = os.path.join(tmp_dir, f"clip_{i+1}.mp4")
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

    def analyze_video(self, video_path: str, output_path: str = None) -> dict:
        """
        High-level method to analyze a video file.

        This method:
          1. Splits the video into clips of length defined by the instance's clip_length_minutes.
          2. Processes each clip using `analyze_clip`, displaying a progress bar.
          3. Merges and post-processes the results.
          4. Optionally saves the results to a JSON file if output_path is provided.

        Args:
          video_path: Path to the video file.
          output_path: Optional file path to save the JSON results.

        Returns:
          A dictionary containing the structured analysis results.
        """
        prompt = self.config.get("prompt", "Analyze this FSD video for interesting events and disengagements.")
        prompt = prompt.format(clip_length_minutes=self.clip_length_minutes, clip_length_seconds=self.clip_length_minutes * 60)
        duration_seconds = self._get_video_duration(video_path)
        clip_paths = self._split_video_into_clips(video_path, duration_seconds, self.clip_length_minutes)
        clip_outputs = []
        for clip in tqdm(clip_paths, desc="Analyzing video"):
            result = self.analyze_clip(clip, prompt)
            clip_outputs.append(result)
        from fsd_tracker_pro.post_processor import postprocess_clip_outputs, save_results_to_json
        results = postprocess_clip_outputs(clip_outputs=clip_outputs,
                                           prompt=prompt,
                                           model_name=self.config.get("model", "gemini-2.0-flash"), 
                                           duration_seconds=duration_seconds, 
                                           clip_length_minutes=self.clip_length_minutes)
        if output_path:
            save_results_to_json(results, output_path)
        return results 

    # Added asynchronous methods for improved performance
    async def analyze_clip_async(self, i: int, clip_path: str, prompt: str) -> list[Analysis]:
        async with self.semaphore:
            uploaded_file = await self._retry_on_connection_reset_async(lambda: self.client.aio.files.upload(file=clip_path))
            while uploaded_file.state != "ACTIVE":
                await asyncio.sleep(self.retry_wait)
                uploaded_file = await self._retry_on_connection_reset_async(lambda: self.client.aio.files.get(name=uploaded_file.name))
            file_uri = uploaded_file.uri
            mime_type = uploaded_file.mime_type
            model = self.config.get("model", "gemini-2.0-flash")
                
            response = await self._retry_on_connection_reset_async(lambda: self.client.aio.models.generate_content(
                model=model,
                contents=[
                types.Part.from_text(text=prompt),
                types.Part.from_uri(file_uri=file_uri, mime_type=mime_type)
            ],
            config={
                'response_mime_type': 'application/json',
                    'response_schema': list[Analysis],
                    'temperature': 0.0
                },
            ))

            # finished, delete the file
            await self._retry_on_connection_reset_async(lambda: self.client.aio.files.delete(name=uploaded_file.name))

        return (i, response.parsed) if response and hasattr(response, "parsed") else (i, [])

    async def analyze_video_async(self, video_path: str, output_path: str = None) -> dict:
        prompt = self.config.get("prompt", "Analyze this FSD video for interesting events and disengagements.")
        prompt = prompt.format(clip_length_minutes=self.clip_length_minutes, clip_length_seconds=self.clip_length_minutes * 60)
        duration_seconds = self._get_video_duration(video_path)
        clip_paths = self._split_video_into_clips(video_path, duration_seconds, self.clip_length_minutes)
        tasks = [asyncio.create_task(self.analyze_clip_async(i, clip, prompt)) for i, clip in enumerate(clip_paths)]
        clip_outputs = []
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Analyzing video"):
            result = await task
            clip_outputs.append(result)

        # restore the order of the clips results, since the async task may return in a different order
        clip_outputs = list(map(lambda x: x[1], sorted(clip_outputs, key=lambda x: x[0])))

        from fsd_tracker_pro.post_processor import postprocess_clip_outputs, save_results_to_json
        results = postprocess_clip_outputs(
            clip_outputs=clip_outputs, 
            prompt=prompt,
            model_name=self.config.get("model", "gemini-2.0-flash"), 
            duration_seconds=duration_seconds, 
            clip_length_minutes=self.clip_length_minutes
        )
        if output_path:
            save_results_to_json(results, output_path)
        return results 