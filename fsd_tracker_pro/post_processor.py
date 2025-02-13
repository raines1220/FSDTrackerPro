import json
from typing import List
from fsd_tracker_pro.response_model import Analysis

def postprocess_clip_outputs(clip_outputs: List[List[Analysis]],
                             prompt: str,
                             model_name: str,
                             duration_seconds: int, 
                             clip_length_minutes: int) -> dict:
    """
    Given the list of LLM raw text analysis for each clip,
    do any logic needed to turn them into structured data.
    """

    format_time = lambda x: f"{int(x // 60):02d}:{int(x % 60):02d}"
    structured_data = {
        "version": "0.1",
        "model_used": model_name,
        "prompt_used": prompt,
        "summary": {},
        "results": []
    }

    for i, output in enumerate(clip_outputs):
        if type(output) != list or len(output) == 0:
            continue
        clip_start_seconds = i * clip_length_minutes * 60
        clip_info = [
            {
                "timestamp": format_time(event.timestamp + clip_start_seconds),
                "description": event.description,
                "event_type": event.event_type.value,
                "driver_action": event.driver_action.value
            } for event in output]
        
        structured_data["results"].extend(clip_info)

    summary = {
        "total_duration": format_time(duration_seconds),
        "events":{
            "total_events": len(structured_data["results"]),
            "positive_events": sum(1 for event in structured_data["results"] if event["event_type"].startswith("Positive:")),
            "negative_events": sum(1 for event in structured_data["results"] if event["event_type"].startswith("Negative:")),
            "interventions": sum(1 for event in structured_data["results"] if event["driver_action"] == "Intervened/Disengaged"),
        }
    }
    structured_data["summary"] = summary
    return structured_data

def save_results_to_json(results: dict, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2) 