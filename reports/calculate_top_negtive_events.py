import os
import sys
import json
import glob
import re
import matplotlib.pyplot as plt

# Go up one directory so that "fsd_tracker_pro" is recognized
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from fsd_tracker_pro.response_model import Event

def convert_duration_to_seconds(duration_str):
    """
    Converts a duration string in the format MM:SS or HH:MM:SS to total seconds.
    If conversion fails, returns 60 as the default.
    """
    try:
        parts = duration_str.split(':')
        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + int(seconds)
        elif len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        else:
            return 60
    except Exception as e:
        return 60

def parse_version(filename):
    """
    Extracts major, minor, fix version from filename containing a version like v11.4.3.
    Returns a tuple (major, minor, fix) or None if not found.
    """
    pattern = r'v(\d+(?:\.\d+){2,})'
    match = re.search(pattern, filename)
    if not match:
        return None
    version_str = match.group(1)  # e.g., "11.4.3"
    parts = version_str.split('.')
    if len(parts) < 3:
        return None
    return parts[0], parts[1], parts[2]

def main():
    # Determine the results folder relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.normpath(os.path.join(base_dir, '../results'))
    json_files = glob.glob(os.path.join(results_dir, '*.json'))
    
    if not json_files:
        print(f"No JSON files found in {results_dir}")
        return

    # Initialize groups for v11, v12, v13.
    # We add a "duration" key to accumulate the total duration (in seconds) for each version.
    groups = {
        '11': {'counts': {}, 'safety': {}, 'duration': 0},
        '12': {'counts': {}, 'safety': {}, 'duration': 0},
        '13': {'counts': {}, 'safety': {}, 'duration': 0}
    }

    for filepath in json_files:
        filename = os.path.basename(filepath)
        version_parts = parse_version(filename)
        if not version_parts:
            print(f"Could not parse version from {filename}")
            continue
        major, minor, fix = version_parts
        if major not in groups:
            continue  # Only process v11, v12, v13

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed to read {filepath}: {e}")
            continue

        # Check for a duration field at the top level.
        # If missing or invalid, look in summary.total_duration.
        duration = data.get('duration')
        if duration is None or not isinstance(duration, (int, float)) or duration <= 0:
            duration_str = data.get('summary', {}).get('total_duration')
            if duration_str:
                duration = convert_duration_to_seconds(duration_str)
            else:
                print(f"Missing or invalid duration in {filename}. Assuming default duration of 60 seconds.")
                duration = 60.0
        groups[major]['duration'] += duration

        if 'results' not in data:
            print(f"No 'results' found in {filename}")
            continue

        for event in data.get('results', []):
            event_str = event.get('event_type', '')
            # Skip positive events
            if isinstance(event_str, str) and event_str.startswith("Positive:"):
                continue

            try:
                evt = Event.from_string(event_str)
            except Exception as e:
                print(f"Failed to parse event_type '{event_str}': {e}")
                continue

            groups[major]['counts'][event_str] = groups[major]['counts'].get(event_str, 0) + 1
            if event_str not in groups[major]['safety']:
                try:
                    groups[major]['safety'][event_str] = evt.is_safety_related()
                except Exception as e:
                    groups[major]['safety'][event_str] = False

    versions = ['11', '12', '13']
    for ver in reversed(versions):
        counts_dict = groups[ver]['counts']
        safety_dict = groups[ver]['safety']
        total_duration = groups[ver]['duration']
        # Create a new figure for each version
        plt.figure(figsize=(10, 7))
        if not counts_dict or total_duration == 0:
            plt.text(0.5, 0.5, f'No events for v{ver}', horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
            plt.title(f'v{ver}')
            plt.axis('off')
        else:
            # Get the top 10 negative events sorted by raw count in descending order.
            top_events = sorted(counts_dict.items(), key=lambda x: x[1], reverse=True)[:10]
            event_types = [item[0] for item in top_events]
            # Remove 'Negative:' prefix for display.
            labels = [et.replace("Negative:", "").strip() if et.startswith("Negative:") else et for et in event_types]
            raw_counts = [item[1] for item in top_events]
            
            # Normalize counts based on the total duration (converted to hours).
            # Frequency (events per hour) = (raw_count * 3600) / total_duration.
            normalized_counts = [(count * 3600) / total_duration for count in raw_counts]
            
            # Set colors: pure red for safety related events, 'dodgerblue' for others.
            colors = [(1, 0, 0) if safety_dict.get(et, False) else "dodgerblue" for et in event_types]
            
            y_positions = range(len(normalized_counts))
            plt.barh(y_positions, normalized_counts, color=colors)
            plt.yticks(y_positions, labels)
            plt.gca().invert_yaxis()  # highest frequencies at the top
            plt.xlabel("Events per hour")
            plt.title(f"Top 10 Negative Events - v{ver}")
            
            # Annotate each bar with its normalized frequency (formatted to 2 decimals)
            max_val = max(normalized_counts)
            for j, freq in enumerate(normalized_counts):
                plt.text(freq + max_val * 0.01, j, f"{freq:.2f}", color="black", va="center")
        plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()