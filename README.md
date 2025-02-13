# FSD Tracker Pro

FSD Tracker Pro is an advanced video analysis tool that leverages Google's Generative AI API to identify interesting events and disengagements in your videos. The application processes videos asynchronously by splitting them into clips and analyzing each clip individually, with aggregated results for comprehensive insights.

## Features

- **Asynchronous Processing:** Leverages asynchronous file uploads and inference to rapidly analyze videos.
- **Concurrency Control:** Uses asyncio.Semaphore to efficiently manage concurrent API requests.
- **Configurable:** Easily adjust video clip lengths, model parameters, and more via a configuration file.
- **Video Splitting:** Automatically splits videos into manageable clips for detailed analysis.
- **Post-Processing:** Cleans up and formats analysis outputs to generate actionable insights.
- **Reporting Tools:** Includes scripts to generate detailed reports on event metrics from analyzed videos.
- **Result Storage:** Saves analysis outputs in JSON format for further analysis and review.

## Requirements

- Python 3.7 or higher

Install dependencies using pip:

```bash
pip install -r requirements.txt
```

## Setup

1. **Environment Variables:** Create a `.env` file in the project root and define your `GEMINI_API_KEY`:

   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

2. **Configuration:** Update `config.yaml` in the project root to adjust settings such as clip length and model parameters.

3. **Running the Analysis:** Execute the main script with the path to your video file:

   ```bash
   python main.py path_to_video.mp4
   ```

## Generating Reports

After processing videos, analysis results are stored in the `results/` directory in JSON format. Use the scripts in the `reports/` directory to generate insightful metrics:

- Generate top negative events:
  ```bash
  python reports/calculate_top_negtive_events.py
  ```
- Calculate positive event ratios:
  ```bash
  python reports/calculate_positive_ratio.py
  ```
- Compute hours per intervention:
  ```bash
  python reports/calculate_hour_per_intervention.py
  ```

## Live Demo

Experience a live demonstration of the analysis on our website: [fsdtracker.pro](https://fsdtracker.pro)

## Project Structure

- `fsd_tracker_pro/`
  - `video_analyzer.py`: Core module for processing and analyzing video files using the Gemini API.
  - `post_processor.py`: Handles post-processing and formatting of the analysis results.
  - `response_model.py`: Defines data models for API responses.
  - `video_splitter.py`: Utility module for splitting videos into clips.
  - `config_reader.py`: Reads and parses configuration settings from `config.yaml`.
- `reports/`
  - `calculate_top_negtive_events.py`: Script to generate a report of top negative events detected.
  - `calculate_positive_ratio.py`: Script to compute the ratio of positive events.
  - `calculate_hour_per_intervention.py`: Script to calculate the hours per intervention from analysis data.
- `results/`: Directory containing JSON files with analysis outputs for each processed video.
- `main.py`: Entry point for initiating video analysis.