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

def main():
    st.title("Video Subtitling and Translation Tool")
    st.write("Upload a video to generate subtitles and translations")

    # File size warnings and information
    st.warning(f"⚠️ File size limit: {MediaService.MAX_FILE_SIZE_MB}MB")
    st.info("""
    Tips for handling large videos:
    - Trim your video to include only the necessary parts
    - Use a video compression tool before uploading
    - Consider splitting long videos into smaller segments
    """)

    # File uploader with completely custom help text
    video_file = st.file_uploader(
        "Choose a video file",
        type=SUPPORTED_VIDEO_FORMATS,
        help=f"Upload your video file here (Maximum size: {MediaService.MAX_FILE_SIZE_MB}MB)\nSupported formats: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
    )

    if video_file is not None:
        # Initialize temp_dir as None for proper error handling
        temp_dir = None
        try:
            # Check file size before processing
            file_size_mb = len(video_file.getbuffer()) / (1024 * 1024)
            if file_size_mb > MediaService.MAX_FILE_SIZE_MB:
                st.error(f"File size ({file_size_mb:.1f}MB) exceeds the maximum limit of {MediaService.MAX_FILE_SIZE_MB}MB.")
                st.info("Please compress your video or split it into smaller segments before uploading.")
                return

            # Save uploaded file temporarily
            temp_dir = tempfile.mkdtemp()
            temp_video_path = os.path.join(temp_dir, video_file.name)
            with open(temp_video_path, "wb") as f:
                f.write(video_file.getbuffer())

            # Extract audio
            try:
                with st.spinner("Extracting and compressing audio from video..."):
                    audio_path = media_service.extract_audio(temp_video_path)
            except ValueError as e:
                st.error(str(e))
                if temp_dir:
                    media_service.cleanup_temp_files([temp_dir])
                return
            except Exception as e:
                st.error(f"Error processing audio: {str(e)}")
                if temp_dir:
                    media_service.cleanup_temp_files([temp_dir])
                return

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

            if st.button("Generate Subtitles and Translation"):
                try:
                    # Transcribe audio
                    with st.spinner("Transcribing audio..."):
                        original_segments = openai_service.transcribe_audio(audio_path)
                    
                    # Create original language subtitles
                    if subtitle_format == 'srt':
                        original_subtitles = subtitle_service.create_srt(original_segments)
                    else:
                        original_subtitles = subtitle_service.create_vtt(original_segments)

                    # Translate subtitles
                    with st.spinner("Translating subtitles..."):
                        translated_segments = []
                        progress_bar = st.progress(0)
                        
                        for i, segment in enumerate(original_segments):
                            translated_text = openai_service.translate_text(
                                segment['text'],
                                SUPPORTED_LANGUAGES[target_language]
                            )
                            translated_segments.append({
                                'start': segment['start'],
                                'end': segment['end'],
                                'text': translated_text
                            })
                            progress_bar.progress((i + 1) / len(original_segments))

                    # Create translated subtitles
                    if subtitle_format == 'srt':
                        translated_subtitles = subtitle_service.create_srt(translated_segments)
                    else:
                        translated_subtitles = subtitle_service.create_vtt(translated_segments)

                    # Download buttons
                    st.subheader("Download Subtitles")
                    
                    # Original subtitles
                    st.download_button(
                        label="Download Original Subtitles",
                        data=original_subtitles,
                        file_name=f"original.{subtitle_format}",
                        mime="text/plain"
                    )

                    # Translated subtitles
                    st.download_button(
                        label=f"Download {target_language} Subtitles",
                        data=translated_subtitles,
                        file_name=f"translated_{SUPPORTED_LANGUAGES[target_language]}.{subtitle_format}",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                finally:
                    # Cleanup
                    if temp_dir:
                        media_service.cleanup_temp_files([temp_dir, audio_path])

        except Exception as e:
            st.error(f"An error occurred while processing the video: {str(e)}")
            if temp_dir:
                media_service.cleanup_temp_files([temp_dir])

if __name__ == "__main__":
    main()
