import streamlit as st
import os
import tempfile
from services.openai_service import OpenAIService
from services.media_service import MediaService
from services.subtitle_service import SubtitleService
from utils.constants import SUPPORTED_LANGUAGES, SUPPORTED_VIDEO_FORMATS, SUPPORTED_SUBTITLE_FORMATS
import time

# Initialize services
openai_service = OpenAIService()
media_service = MediaService()
subtitle_service = SubtitleService()

def process_single_video(video_file, target_language, subtitle_format):
    """Process a single video file and return subtitles"""
    temp_dir = None
    try:
        # Check file size
        file_size_mb = len(video_file.getbuffer()) / (1024 * 1024)
        if file_size_mb > MediaService.MAX_FILE_SIZE_MB:
            return None, None, f"File {video_file.name} ({file_size_mb:.1f}MB) exceeds the maximum limit of {MediaService.MAX_FILE_SIZE_MB}MB."

        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_video_path = os.path.join(temp_dir, video_file.name)
        with open(temp_video_path, "wb") as f:
            f.write(video_file.getbuffer())

        # Extract audio
        audio_path = media_service.extract_audio(temp_video_path)

        # Transcribe audio
        original_segments = openai_service.transcribe_audio(audio_path)
        
        # Create original language subtitles
        if subtitle_format == 'srt':
            original_subtitles = subtitle_service.create_srt(original_segments)
        else:
            original_subtitles = subtitle_service.create_vtt(original_segments)

        # Translate subtitles
        translated_segments = []
        for segment in original_segments:
            translated_text = openai_service.translate_text(
                segment['text'],
                SUPPORTED_LANGUAGES[target_language]
            )
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': translated_text
            })

        # Create translated subtitles
        if subtitle_format == 'srt':
            translated_subtitles = subtitle_service.create_srt(translated_segments)
        else:
            translated_subtitles = subtitle_service.create_vtt(translated_segments)

        return original_subtitles, translated_subtitles, None

    except Exception as e:
        return None, None, str(e)
    finally:
        # Cleanup
        if temp_dir:
            media_service.cleanup_temp_files([temp_dir])

def main():
    st.title("Video Subtitling and Translation Tool")
    st.write("Upload videos to generate subtitles and translations")

    # File size warnings and information
    st.warning(f"⚠️ File size limit: {MediaService.MAX_FILE_SIZE_MB}MB per video")
    st.info("""
    Tips for handling large videos:
    - Trim your videos to include only the necessary parts
    - Use a video compression tool before uploading
    - Consider splitting long videos into smaller segments
    """)

    # Multi-file uploader
    video_files = st.file_uploader(
        "Choose video files",
        type=SUPPORTED_VIDEO_FORMATS,
        accept_multiple_files=True,
        help=f"Upload your video files here (Maximum size: {MediaService.MAX_FILE_SIZE_MB}MB per file)\nSupported formats: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
    )

    if video_files:
        st.write(f"Selected {len(video_files)} video(s) for processing")

        # Transcription settings
        st.subheader("Transcription and Translation Settings")
        target_language = st.selectbox(
            "Select target language for translation",
            options=list(SUPPORTED_LANGUAGES.keys())
        )

        subtitle_format = st.selectbox(
            "Select subtitle format",
            options=SUPPORTED_SUBTITLE_FORMATS
        )

        if st.button("Process All Videos"):
            # Create a container for the progress
            progress_container = st.container()
            
            # Process each video
            for i, video_file in enumerate(video_files, 1):
                with progress_container:
                    st.write(f"Processing video {i}/{len(video_files)}: {video_file.name}")
                    progress_bar = st.progress(0)
                    
                    # Process the video
                    original_subtitles, translated_subtitles, error = process_single_video(
                        video_file, target_language, subtitle_format
                    )
                    
                    if error:
                        st.error(f"Error processing {video_file.name}: {error}")
                        continue
                    
                    # Create a unique container for each video's download buttons
                    st.write(f"Download options for {video_file.name}:")
                    
                    # Original subtitles
                    st.download_button(
                        label=f"Download Original Subtitles - {video_file.name}",
                        data=original_subtitles,
                        file_name=f"{os.path.splitext(video_file.name)[0]}_original.{subtitle_format}",
                        mime="text/plain"
                    )

                    # Translated subtitles
                    st.download_button(
                        label=f"Download {target_language} Subtitles - {video_file.name}",
                        data=translated_subtitles,
                        file_name=f"{os.path.splitext(video_file.name)[0]}_{SUPPORTED_LANGUAGES[target_language]}.{subtitle_format}",
                        mime="text/plain"
                    )
                    
                    progress_bar.progress(1.0)
                    st.success(f"Completed processing {video_file.name}")

if __name__ == "__main__":
    main()
