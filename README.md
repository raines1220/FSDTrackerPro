# FSD Tracker Pro

FSD Tracker Pro is a video analysis tool that leverages Google's Generative AI API to analyze videos for interesting events and disengagements. The tool splits videos into clips, processes each clip individually, and aggregates results into a comprehensive analysis report.

## Features

- **Asynchronous Processing:** Utilizes asynchronous file upload and inference to expedite video analysis.
- **Concurrency Control:** Uses asyncio.Semaphore to manage concurrent API requests.
- **Configurable:** Easily adjust clip length and model parameters via a configuration file.

## Requirements

- Python 3.7 or higher

Install dependencies via pip (example):

```bash
pip install -r requirements.txt
```

## Setup

1. **Environment Variables:** Create a `.env` file in the project root and set your `GEMINI_API_KEY`:

   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

2. **Configuration:** Update `config.yaml` with your desired settings (clip length, model, etc.).

3. **Running the Analysis:** Execute the main script by providing the path to your video file:

   ```bash
   python main.py path_to_video.mp4
   ```

## Live Demo

Get a firsthand look at our analysis results! Visit our live demo site at [fsdtracker.pro](https://fsdtracker.pro) to see FSD Tracker Pro in action.

## Project Structure

- `fsd_tracker_pro/video_analyzer.py`: Contains the `VideoAnalyzer` class for processing video files.
- `fsd_tracker_pro/post_processor.py`: Post-processes and formats analysis output.
- `fsd_tracker_pro/response_model.py`: Data models for analysis responses.
- `fsd_tracker_pro/video_splitter.py`: Utility for splitting videos into clips.
- `fsd_tracker_pro/config_reader.py`: Reads project configuration from a YAML file.
- `main.py`: Entry point for the application.