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

    # File uploader
    video_file = st.file_uploader(
        "Choose a video file",
        type=SUPPORTED_VIDEO_FORMATS
    )

    if video_file is not None:
        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_video_path = os.path.join(temp_dir, video_file.name)
        with open(temp_video_path, "wb") as f:
            f.write(video_file.getbuffer())

        # Extract audio
        with st.spinner("Extracting audio from video..."):
            audio_path = media_service.extract_audio(temp_video_path)

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
                    transcription = openai_service.transcribe_audio(audio_path)
                    original_segments = transcription['segments']
                
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
                media_service.cleanup_temp_files([temp_dir, audio_path])

if __name__ == "__main__":
    main()
