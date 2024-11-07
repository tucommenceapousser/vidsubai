from typing import List
import datetime

class SubtitleService:
    @staticmethod
    def create_srt(segments: List[dict]) -> str:
        """
        Create SRT format subtitles from segments
        """
        srt_content = []
        for i, segment in enumerate(segments, 1):
            start = datetime.timedelta(seconds=segment['start'])
            end = datetime.timedelta(seconds=segment['end'])
            
            # Format timestamp as required by SRT
            start_str = str(start).replace('.', ',')[:12]
            end_str = str(end).replace('.', ',')[:12]
            
            srt_content.append(f"{i}\n{start_str} --> {end_str}\n{segment['text']}\n")
        
        return "\n".join(srt_content)

    @staticmethod
    def create_vtt(segments: List[dict]) -> str:
        """
        Create WebVTT format subtitles from segments
        """
        vtt_content = ["WEBVTT\n"]
        for segment in segments:
            start = datetime.timedelta(seconds=segment['start'])
            end = datetime.timedelta(seconds=segment['end'])
            
            # Format timestamp as required by WebVTT
            start_str = str(start)[:11].replace(',', '.')
            end_str = str(end)[:11].replace(',', '.')
            
            vtt_content.append(f"\n{start_str} --> {end_str}\n{segment['text']}")
        
        return "\n".join(vtt_content)
