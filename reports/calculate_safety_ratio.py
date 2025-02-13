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
    pattern = r'v(\d+(?:\.\d+){1,})'
    match = re.search(pattern, filename)
    if not match:
        return None
    version_str = match.group(1)  # e.g. '11.4.3' or '12.5.6.3'
    parts = version_str.split('.')
    if len(parts) < 2:
        return None
    # Only take first three parts for major, minor, fix
    if len(parts) == 2:
        return parts[0], parts[1], '0'
    return parts[0], parts[1], parts[2]


def extract_data_from_file(filepath):
    """
    Reads a JSON file and extracts overall event statistics:
      total_interventions: the number of events in the "results" list.
      safety_interventions: count of events where event_type starts with "Safety:".
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to read {filepath}: {e}")
        return None, None

    if 'results' not in data:
        print(f"No 'results' found in {filepath}")
        return 0, 0

    total_interventions = 0
    safety_interventions = 0

    for event in data.get('results', []):
        evt_type = Event.from_string(event.get('event_type', ''))
        if event.get('driver_action', '') == 'Intervened/Disengaged':
            total_interventions += 1
            if evt_type.is_safety_related():
                safety_interventions += 1

    return total_interventions, safety_interventions


def main():
    # Determine the results folder from command line argument.
    if len(sys.argv) < 2:
        print("Usage: python calculate_safety_ratio.py <results_folder>")
        return
    results_dir = sys.argv[1]
    json_files = glob.glob(os.path.join(results_dir, '*.json'))

    if not json_files:
        print(f"No JSON files found in {results_dir}")
        return

    # Aggregation dictionaries by version groups.
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

        total_interventions, safety_interventions = extract_data_from_file(filepath)
        if total_interventions is None:
            continue

        key_major = major                  # e.g., "11"
        key_minor = f"{major}.{minor}"     # e.g., "11.4"
        key_fix = f"{major}.{minor}.{fix}"  # e.g., "11.4.3"

        # Update aggregation for major version group.
        if key_major not in aggregations['major']:
            aggregations['major'][key_major] = {'total_interventions': 0, 'safety_interventions': 0, 'count': 0}
        aggregations['major'][key_major]['total_interventions'] += total_interventions
        aggregations['major'][key_major]['safety_interventions'] += safety_interventions
        aggregations['major'][key_major]['count'] += 1

        # Update aggregation for minor version group.
        if key_minor not in aggregations['minor']:
            aggregations['minor'][key_minor] = {'total_interventions': 0, 'safety_interventions': 0, 'count': 0}
        aggregations['minor'][key_minor]['total_interventions'] += total_interventions
        aggregations['minor'][key_minor]['safety_interventions'] += safety_interventions
        aggregations['minor'][key_minor]['count'] += 1

        # Update aggregation for fix version group.
        if key_fix not in aggregations['fix']:
            aggregations['fix'][key_fix] = {'total_interventions': 0, 'safety_interventions': 0, 'count': 0}
        aggregations['fix'][key_fix]['total_interventions'] += total_interventions
        aggregations['fix'][key_fix]['safety_interventions'] += safety_interventions
        aggregations['fix'][key_fix]['count'] += 1

    # Print aggregated report for the safety interventions ratio.
    print("Safety Interventions Ratio (Safety interventions / Total Interventions):")
    for version_type in ['major', 'minor', 'fix']:
        print(f"\nFor {version_type} version groups:")
        for ver, stats in sorted(aggregations[version_type].items(), key=lambda x: tuple(map(int, x[0].split('.')))):
            total = stats['total_interventions']
            if total > 0:
                ratio = (stats['safety_interventions'] / total) * 100
                print(
                    f"FSD v{ver.replace('.0', '')}: {ratio:.2f}% safety interventions "
                    f"(Safety: {stats['safety_interventions']}, Total Interventions: {total})"
                )
            else:
                print(f"FSD v{ver.replace('.0', '')}: No events recorded (Total Interventions: {total})")

    # Interactive paging charts: one chart visible at a time with Previous/Next buttons.
    pages = ['major', 'minor', 'fix']
    current_page = 0

    fig = plt.figure(figsize=(10, 7))
    ax_chart = fig.add_axes([0.1, 0.3, 0.8, 0.65])
    axprev = fig.add_axes([0.1, 0.1, 0.2, 0.075])
    axnext = fig.add_axes([0.7, 0.1, 0.2, 0.075])
    button_prev = Button(axprev, 'Previous')
    button_next = Button(axnext, 'Next')

    def draw_page(page_idx):
        ax_chart.cla()
        version_type = pages[page_idx]
        version_labels = []
        safety_ratios = []

        sorted_items = sorted(aggregations[version_type].items(), key=lambda x: tuple(map(int, x[0].split('.'))))
        for ver, stats in sorted_items:
            total = stats['total_interventions']
            ratio = (stats['safety_interventions'] / total) * 100 if total > 0 else 0
            version_labels.append(f"FSD v{ver.replace('.0', '')}")
            safety_ratios.append(ratio)
        
        if safety_ratios:
            min_ratio = min(safety_ratios)
            max_ratio = max(safety_ratios)
            range_ratio = max_ratio - min_ratio if (max_ratio - min_ratio) > 0 else 1
            norm_ratios = [(r - min_ratio) / range_ratio for r in safety_ratios]
            colors = [(1, 0.8 * (1 - norm), 0.8 * (1 - norm)) for norm in norm_ratios]
        else:
            colors = []
        
        bars = ax_chart.bar(version_labels, safety_ratios, color=colors)
        
        for bar in bars:
            height = bar.get_height()
            ax_chart.annotate(f'{height:.2f}%',
                              xy=(bar.get_x() + bar.get_width() / 2, height),
                              xytext=(0, 3),
                              textcoords="offset points",
                              ha='center', va='bottom')
        
        ax_chart.set_title(f'{version_type.capitalize()} Version Groups - Safety Interventions Ratio')
        ax_chart.set_xlabel('FSD Version')
        ax_chart.set_ylabel('Safety Intervention Ratio (%)')
        ax_chart.tick_params(axis='x', rotation=45)
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
    
    draw_page(current_page)
    plt.show()


if __name__ == '__main__':
    main() 