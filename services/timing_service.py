from typing import List, Dict, Any
import datetime

class TimingService:
    @staticmethod
    def adjust_global_offset(segments: List[Dict[str, Any]], offset_seconds: float) -> List[Dict[str, Any]]:
        """
        Adjust all subtitle timings by adding/subtracting a global offset
        """
        adjusted_segments = []
        for segment in segments:
            adjusted_segments.append({
                'start': max(0, segment['start'] + offset_seconds),
                'end': max(0, segment['end'] + offset_seconds),
                'text': segment['text']
            })
        return adjusted_segments

    @staticmethod
    def adjust_duration_scale(segments: List[Dict[str, Any]], scale_factor: float) -> List[Dict[str, Any]]:
        """
        Scale the duration of all subtitles by a factor
        """
        adjusted_segments = []
        for segment in segments:
            duration = segment['end'] - segment['start']
            new_duration = duration * scale_factor
            adjusted_segments.append({
                'start': segment['start'],
                'end': segment['start'] + new_duration,
                'text': segment['text']
            })
        return adjusted_segments

    @staticmethod
    def adjust_segment_timing(segments: List[Dict[str, Any]], segment_index: int, 
                            new_start: float = None, new_end: float = None) -> List[Dict[str, Any]]:
        """
        Adjust timing for a specific subtitle segment
        """
        if segment_index < 0 or segment_index >= len(segments):
            raise ValueError("Invalid segment index")

        adjusted_segments = segments.copy()
        if new_start is not None:
            adjusted_segments[segment_index]['start'] = max(0, new_start)
        if new_end is not None:
            adjusted_segments[segment_index]['end'] = max(new_start, new_end)

        return adjusted_segments
