import os
import re
import sys
import json
import glob
import matplotlib.pyplot as plt
from matplotlib.widgets import Button  # for interactive paging

# Go up one directory so that "fsd_tracker_pro" is recognized
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from fsd_tracker_pro.response_model import Event

def parse_version(filename):
    # Regex to find version numbers like v11.4.3 or v12.5.6.3
    pattern = r'v(\d+(?:\.\d+){2,})'
    match = re.search(pattern, filename)
    if not match:
        return None
    version_str = match.group(1)  # e.g. '11.4.3' or '12.5.6.3'
    parts = version_str.split('.')
    if len(parts) < 3:
        return None
    # Only take first three parts for major, minor, fix
    return parts[0], parts[1], parts[2]


def extract_data_from_file(filepath):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to read {filepath}: {e}")
        return None, None

    # Try to extract duration from top-level keys, then from within summary if needed
    duration_val = data.get('total_duration') or data.get('duration') or data.get('totalDuration')
    if duration_val is None and 'summary' in data:
        duration_val = (
            data["summary"].get('total_duration') or
            data["summary"].get('duration') or
            data["summary"].get('totalDuration')
        )
    
    if duration_val is None:
        print(f"No duration found in {filepath}")
        return None, None

    # Convert duration to seconds.
    # If it's a string with colon separators (e.g., "44:52" or "1:02:30"), parse accordingly.
    try:
        if isinstance(duration_val, (int, float)):
            total_duration = float(duration_val)
        elif isinstance(duration_val, str):
            if ':' in duration_val:
                parts = [float(part) for part in duration_val.split(':')]
                if len(parts) == 2:
                    # Format: MM:SS
                    minutes, seconds = parts
                    total_duration = minutes * 60 + seconds
                elif len(parts) == 3:
                    # Format: HH:MM:SS
                    hours, minutes, seconds = parts
                    total_duration = hours * 3600 + minutes * 60 + seconds
                else:
                    total_duration = float(duration_val)
            else:
                total_duration = float(duration_val)
        else:
            total_duration = float(duration_val)
    except Exception as e:
        print(f"Invalid duration format in {filepath}: {e}")
        return None, None

    # Look for interventions.
    # First try at the top-level and then within summary/events.
    interventions_val = 0
    for event in data.get('results', []):
        if event['driver_action'] == 'Intervened/Disengaged':
            interventions_val += 1

    if interventions_val is None:
        print(f"No interventions found in {filepath}")
        return total_duration, 0

    try:
        interventions_count = int(interventions_val)
    except Exception as e:
        print(f"Invalid interventions format in {filepath}: {e}")
        interventions_count = 0

    return total_duration, interventions_count


def main():
    # Determine the folder for results relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.normpath(os.path.join(base_dir, '../results'))
    json_files = glob.glob(os.path.join(results_dir, '*.json'))

    if not json_files:
        print(f"No JSON files found in {results_dir}")
        return

    # Aggregation dictionaries by version groups.
    # Group by:
    #   - major: key is the major version (e.g. "11")
    #   - minor: key is a combination of major.minor (e.g. "11.4")
    #   - fix: key is a complete version from major.minor.fix (e.g. "11.4.3")
    aggregations = {
        'major': {},
        'minor': {},
        'fix': {}
    }

    for filepath in json_files:
        filename = os.path.basename(filepath)
        version_parts = parse_version(filename)
        if not version_parts:
            print(f"Could not parse version from {filename}")
            continue
        major, minor, fix = version_parts

        total_duration, interventions_count = extract_data_from_file(filepath)
        if total_duration is None:
            continue

        # Create composite keys for minor and fix to include the major part.
        key_major = major                      # e.g. "11"
        key_minor = f"{major}.{minor}"         # e.g. "11.4"
        key_fix = f"{major}.{minor}.{fix}"       # e.g. "11.4.3"

        # Update aggregation for major version group
        if key_major not in aggregations['major']:
            aggregations['major'][key_major] = {'total_seconds': 0, 'total_interventions': 0, 'count': 0}
        aggregations['major'][key_major]['total_seconds'] += total_duration
        aggregations['major'][key_major]['total_interventions'] += interventions_count
        aggregations['major'][key_major]['count'] += 1

        # Update aggregation for minor version group
        if key_minor not in aggregations['minor']:
            aggregations['minor'][key_minor] = {'total_seconds': 0, 'total_interventions': 0, 'count': 0}
        aggregations['minor'][key_minor]['total_seconds'] += total_duration
        aggregations['minor'][key_minor]['total_interventions'] += interventions_count
        aggregations['minor'][key_minor]['count'] += 1

        # Update aggregation for fix version group
        if key_fix not in aggregations['fix']:
            aggregations['fix'][key_fix] = {'total_seconds': 0, 'total_interventions': 0, 'count': 0}
        aggregations['fix'][key_fix]['total_seconds'] += total_duration
        aggregations['fix'][key_fix]['total_interventions'] += interventions_count
        aggregations['fix'][key_fix]['count'] += 1

    # Print aggregated report using minutes instead of hours.
    print('Average driving minute between interventions:')
    for version_type in ['major', 'minor', 'fix']:
        print(f"\nFor {version_type} version groups:")
        for ver, stats in sorted(aggregations[version_type].items(), key=lambda x: tuple(map(int, x[0].split('.')))):
            total_minutes = stats['total_seconds'] / 60
            if stats['total_interventions'] > 0:
                avg_minutes = total_minutes / stats['total_interventions']
                print(
                    f"FSD v{ver}: {avg_minutes:.2f} average driving minutes per intervention "
                    f"(Total: {total_minutes:.2f} minute(s))"
                )
            else:
                print(f"FSD v{ver}: No interventions recorded (Total: {total_minutes:.2f} minute(s))")

    # Interactive paging charts: one chart visible at a time with Previous/Next buttons.
    pages = ['major', 'minor', 'fix']
    current_page = 0

    # Create the figure and the main chart axis.
    fig = plt.figure(figsize=(10, 7))
    ax_chart = fig.add_axes([0.1, 0.3, 0.8, 0.65])
    # Button axes for navigation.
    axprev = fig.add_axes([0.1, 0.1, 0.2, 0.075])
    axnext = fig.add_axes([0.7, 0.1, 0.2, 0.075])
    button_prev = Button(axprev, 'Previous')
    button_next = Button(axnext, 'Next')

    def draw_page(page_idx):
        ax_chart.cla()  # clear the current chart
        version_type = pages[page_idx]
        version_labels = []
        avg_minutes_values = []
        # Sort the version keys numerically (e.g. "11", "11.4", "11.4.3")
        sorted_items = sorted(
            aggregations[version_type].items(),
            key=lambda x: tuple(map(int, x[0].split('.')))
        )
        for ver, stats in sorted_items:
            if stats['total_interventions'] > 0:
                avg = (stats['total_seconds'] / 60) / stats['total_interventions']
            else:
                avg = 0
            version_labels.append(f"FSD v{ver}")
            avg_minutes_values.append(avg)
        
        # Draw the bar chart and capture the bar containers.
        bars = ax_chart.bar(version_labels, avg_minutes_values, color='skyblue')
        
        # Annotate each bar with the exact number.
        for bar in bars:
            height = bar.get_height()
            ax_chart.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{height:.2f}",
                ha='center',
                va='bottom'
            )
        
        ax_chart.set_title(f'{version_type.capitalize()} Version Groups')
        ax_chart.set_xlabel('FSD Version')
        ax_chart.set_ylabel('Avg Driving Minutes per Intervention')
        ax_chart.tick_params(axis='x', rotation=45)
        fig.canvas.draw_idle()

    def next_page(event):
        nonlocal current_page
        current_page = (current_page + 1) % len(pages)
        draw_page(current_page)

    def prev_page(event):
        nonlocal current_page
        current_page = (current_page - 1) % len(pages)
        draw_page(current_page)

    button_next.on_clicked(next_page)
    button_prev.on_clicked(prev_page)

    # Draw the initial page.
    draw_page(current_page)
    plt.show()


if __name__ == '__main__':
    main() 