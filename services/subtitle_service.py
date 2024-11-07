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

    @staticmethod
    def create_ass(segments: List[dict]) -> str:
        """
        Create ASS/SSA format subtitles from segments
        """
        ass_header = """[Script Info]
ScriptType: v4.00+
PlayResY: 384
PlayResX: 512
Collisions: Normal

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        ass_content = [ass_header]
        
        for segment in segments:
            start = datetime.timedelta(seconds=segment['start'])
            end = datetime.timedelta(seconds=segment['end'])
            
            # Format timestamp as required by ASS (h:mm:ss.cc)
            start_str = str(start)[:11].replace('.', ':')
            end_str = str(end)[:11].replace('.', ':')
            
            # Format text and escape commas
            text = segment['text'].replace(',', '\\N')
            
            ass_content.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")
        
        return "\n".join(ass_content)

    @staticmethod
    def create_sub(segments: List[dict], fps: float = 23.976) -> str:
        """
        Create MicroDVD SUB format subtitles from segments
        """
        sub_content = []
        for segment in segments:
            # Convert seconds to frames
            start_frame = int(segment['start'] * fps)
            end_frame = int(segment['end'] * fps)
            
            # Format text, replace line breaks with |
            text = segment['text'].replace('\n', '|')
            
            sub_content.append(f"{{{start_frame}}}{{{end_frame}}}{text}")
        
        return "\n".join(sub_content)

    @staticmethod
    def create_subtitles(segments: List[dict], format: str, fps: float = 23.976) -> str:
        """
        Create subtitles in the specified format
        """
        format_functions = {
            'srt': SubtitleService.create_srt,
            'vtt': SubtitleService.create_vtt,
            'ass': SubtitleService.create_ass,
            'sub': lambda segs: SubtitleService.create_sub(segs, fps)
        }
        
        if format not in format_functions:
            raise ValueError(f"Unsupported subtitle format: {format}")
            
        return format_functions[format](segments)
