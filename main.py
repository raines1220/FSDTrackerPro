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
        print("Usage: python main.py <path_to_video_1> <path_to_video_2> ...")
        sys.exit(1)

    input_video_paths = sys.argv[1:]
    valid_video_paths = []
    for video_path in input_video_paths:
        if not os.path.isfile(video_path):
            print(f"Error: {video_path} does not exist or is not a file. Skipping.")
        else:
            valid_video_paths.append(video_path)

    if not valid_video_paths:
        print("No valid video files provided.")
        sys.exit(1)

    # Load configuration
    config = read_config("config.yaml")

    # Create VideoAnalyzer instance
    analyzer = VideoAnalyzer(api_key=os.environ.get("GEMINI_API_KEY"), config=config)

    # Ensure output directory exists
    os.makedirs("results", exist_ok=True)

    # Define an async function to process videos sequentially instead of concurrently
    async def process_videos_sequentially():
        for video_path in valid_video_paths:
            result = await analyzer.analyze_video_async(video_path)

            filename = os.path.basename(video_path)
            output_path = os.path.join("results", f"{filename}.json")
            with open(output_path, "w") as outfile:
                json.dump(result, outfile, indent=4)
            print(f"Done! Results for '{video_path}' saved to '{output_path}'.")

    # Run the sequential processing function
    asyncio.run(process_videos_sequentially())


if __name__ == "__main__":
    main() 