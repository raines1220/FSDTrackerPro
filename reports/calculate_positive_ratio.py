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
    """
    Extracts the major, minor, and fix version numbers from a filename.
    For example, a filename containing v11.4.3 will return ('11', '4', '3').
    """
    pattern = r'v(\d+(?:\.\d+){2,})'
    match = re.search(pattern, filename)
    if not match:
        return None
    version_str = match.group(1)  # e.g., "11.4.3" or "12.5.6.3"
    parts = version_str.split('.')
    if len(parts) < 3:
        return None
    # Only take the first three parts for major, minor, fix
    return parts[0], parts[1], parts[2]

def extract_data_from_file(filepath):
    """
    Reads a JSON file and extracts overall event statistics:
      total_events: the number of events in the "results" list.
      positive_events: count of events where event_type starts with "Positive:".
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to read {filepath}: {e}")
        return None, None

    # Check if the JSON has a "results" key.
    if 'results' not in data:
        print(f"No 'results' found in {filepath}")
        return 0, 0

    total_events = 0
    positive_events = 0

    for event in data.get('results', []):
        total_events += 1
        evt_type = event.get('event_type', '')
        if isinstance(evt_type, str) and evt_type.startswith("Positive:"):
            positive_events += 1

    return total_events, positive_events

def main():
    # Determine the results folder relative to this script.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.normpath(os.path.join(base_dir, '../results'))
    json_files = glob.glob(os.path.join(results_dir, '*.json'))

    if not json_files:
        print(f"No JSON files found in {results_dir}")
        return

    # Aggregation dictionaries by version groups.
    # The keys for each group will be:
    #   - major: e.g., "11"
    #   - minor: e.g., "11.4"
    #   - fix: e.g., "11.4.3"
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

        total_events, positive_events = extract_data_from_file(filepath)
        # If extraction fails, skip the file.
        if total_events is None:
            continue

        # Composite keys for minor and fix include the major part.
        key_major = major                  # e.g., "11"
        key_minor = f"{major}.{minor}"     # e.g., "11.4"
        key_fix = f"{major}.{minor}.{fix}"  # e.g., "11.4.3"

        # Update aggregation for major version group.
        if key_major not in aggregations['major']:
            aggregations['major'][key_major] = {'total_events': 0, 'positive_events': 0, 'count': 0}
        aggregations['major'][key_major]['total_events'] += total_events
        aggregations['major'][key_major]['positive_events'] += positive_events
        aggregations['major'][key_major]['count'] += 1

        # Update aggregation for minor version group.
        if key_minor not in aggregations['minor']:
            aggregations['minor'][key_minor] = {'total_events': 0, 'positive_events': 0, 'count': 0}
        aggregations['minor'][key_minor]['total_events'] += total_events
        aggregations['minor'][key_minor]['positive_events'] += positive_events
        aggregations['minor'][key_minor]['count'] += 1

        # Update aggregation for fix version group.
        if key_fix not in aggregations['fix']:
            aggregations['fix'][key_fix] = {'total_events': 0, 'positive_events': 0, 'count': 0}
        aggregations['fix'][key_fix]['total_events'] += total_events
        aggregations['fix'][key_fix]['positive_events'] += positive_events
        aggregations['fix'][key_fix]['count'] += 1

    # Print aggregated report for the positive ratio.
    print("Positive Events Ratio (Positive events / Total events):")
    for version_type in ['major', 'minor', 'fix']:
        print(f"\nFor {version_type} version groups:")
        # Sorting keys numerically for proper ordering.
        for ver, stats in sorted(aggregations[version_type].items(), key=lambda x: tuple(map(int, x[0].split('.')))):
            total = stats['total_events']
            if total > 0:
                ratio = (stats['positive_events'] / total) * 100
                print(
                    f"FSD v{ver}: {ratio:.2f}% positive events "
                    f"(Positive: {stats['positive_events']}, Total: {total})"
                )
            else:
                print(f"FSD v{ver}: No events recorded (Total: {total})")

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
        ax_chart.cla()  # Clear the current chart.
        version_type = pages[page_idx]
        version_labels = []
        positive_ratios = []

        # Sort the keys numerically (e.g., "11", "11.4", "11.4.3")
        sorted_items = sorted(aggregations[version_type].items(), key=lambda x: tuple(map(int, x[0].split('.'))))
        for ver, stats in sorted_items:
            total = stats['total_events']
            ratio = (stats['positive_events'] / total) * 100 if total > 0 else 0
            version_labels.append(f"FSD v{ver}")
            positive_ratios.append(ratio)
            
        # Compute gradient colors for each bar from red to green.
        colors = [(1 - (ratio/100), (ratio/100), 0) for ratio in positive_ratios]
        
        # Draw the bar chart with the computed colors.
        bars = ax_chart.bar(version_labels, positive_ratios, color=colors)
        
        # Annotate each bar with its percentage value.
        for bar in bars:
            height = bar.get_height()
            ax_chart.annotate(f'{height:.2f}%', 
                              xy=(bar.get_x() + bar.get_width() / 2, height),
                              xytext=(0, 3),  # offset text above the bar
                              textcoords="offset points",
                              ha='center', va='bottom')
        
        ax_chart.set_title(f'{version_type.capitalize()} Version Groups - Positive Ratio')
        ax_chart.set_xlabel('FSD Version')
        ax_chart.set_ylabel('Positive Event Ratio (%)')
        ax_chart.tick_params(axis='x', rotation=45)
        # Force an immediate redraw so that the updated chart shows without needing to close the window.
        fig.canvas.draw()  
        
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
    
    # Optionally, enable interactive mode in case your backend requires it.
    # plt.ion()

    # Draw the initial page.
    draw_page(current_page)
    plt.show()

if __name__ == '__main__':
    main()
