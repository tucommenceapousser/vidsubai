import os
from moviepy.editor import VideoFileClip
import tempfile
from typing import Tuple
import shutil
import subprocess

class MediaService:
    MAX_FILE_SIZE_MB = 25

    @staticmethod
    def check_file_size(file_path: str) -> float:
        """
        Check file size in MB
        """
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)

    @staticmethod
    def compress_audio(input_path: str, output_path: str) -> str:
        """
        Compress audio using ffmpeg with 16kHz mono format
        """
        try:
            command = [
                'ffmpeg', '-y',  # Overwrite output file if it exists
                '-i', input_path,
                '-ar', '16000',  # Set sample rate to 16kHz
                '-ac', '1',      # Convert to mono
                '-c:a', 'pcm_s16le',  # Use 16-bit PCM encoding
                output_path
            ]
            subprocess.run(command, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise Exception(f"Audio compression failed: {str(e)}")

    @staticmethod
    def extract_audio(video_path: str) -> str:
        """
        Extract and compress audio from video file and save as WAV
        """
        # Check input video size
        video_size = MediaService.check_file_size(video_path)
        if video_size > MediaService.MAX_FILE_SIZE_MB:
            raise ValueError(f"Video file size ({video_size:.1f}MB) exceeds the maximum limit of {MediaService.MAX_FILE_SIZE_MB}MB")

        temp_dir = tempfile.mkdtemp()
        temp_audio_path = os.path.join(temp_dir, "temp_audio.wav")
        final_audio_path = os.path.join(temp_dir, "audio.wav")

        try:
            # Extract audio using moviepy
            video = VideoFileClip(video_path)
            audio = video.audio
            audio.write_audiofile(temp_audio_path)
            video.close()
            audio.close()

            # Compress audio using ffmpeg
            MediaService.compress_audio(temp_audio_path, final_audio_path)
            
            # Clean up temporary audio file
            os.remove(temp_audio_path)
            
            # Check final audio size
            audio_size = MediaService.check_file_size(final_audio_path)
            if audio_size > MediaService.MAX_FILE_SIZE_MB:
                raise ValueError(f"Compressed audio file size ({audio_size:.1f}MB) still exceeds the maximum limit")

            return final_audio_path

        except Exception as e:
            # Clean up in case of error
            shutil.rmtree(temp_dir)
            raise e

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
