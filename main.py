import os
import sys
import json
import asyncio
from fsd_tracker_pro import VideoAnalyzer
from fsd_tracker_pro.config_reader import read_config
from dotenv import load_dotenv
load_dotenv()


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_local_video>")
        sys.exit(1)

    video_path = sys.argv[1]
    if not os.path.isfile(video_path):
        print(f"Error: {video_path} does not exist or is not a file.")
        sys.exit(1)

    # Load config
    config = read_config("config.yaml")

    # Create VideoAnalyzer with configuration, API key, and clip length from config.
    analyzer = VideoAnalyzer(api_key=os.environ.get("GEMINI_API_KEY"), config=config)

    # Analyze video using the high-level API.
    results = asyncio.run(analyzer.analyze_video_async(video_path))
    output_path = f"results/{video_path.split('/')[-1]}.json"
    os.makedirs("results", exist_ok=True)
    json.dump(results, open(output_path, "w"), indent=4)

    print(f"Done! Results saved to {output_path}")

if __name__ == "__main__":
    main() 