import os
from moviepy.editor import VideoFileClip
import tempfile
from typing import Tuple
import shutil

class MediaService:
    @staticmethod
    def extract_audio(video_path: str) -> str:
        """
        Extract audio from video file and save as WAV
        """
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "audio.wav")
        
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        
        video.close()
        audio.close()
        
        return audio_path

    @staticmethod
    def get_video_duration(video_path: str) -> float:
        """
        Get video duration in seconds
        """
        video = VideoFileClip(video_path)
        duration = video.duration
        video.close()
        return duration

    @staticmethod
    def cleanup_temp_files(file_paths: list):
        """
        Clean up temporary files and directories
        """
        for path in file_paths:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
