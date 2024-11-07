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

# Initialize session states
if 'download_status' not in st.session_state:
    st.session_state.download_status = {}
if 'processed_videos' not in st.session_state:
    st.session_state.processed_videos = {}

def handle_download(video_key, subtitle_type):
    """Handle download button callback"""
    if f"{subtitle_type}_{video_key}" not in st.session_state:
        st.session_state[f"{subtitle_type}_{video_key}"] = True
    return True

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

def display_download_section(video_files):
    """Display download buttons for processed videos"""
    if not st.session_state.processed_videos:
        return

    st.subheader("Download Processed Subtitles")
    for video_key, video_data in st.session_state.processed_videos.items():
        with st.expander(f"Download options for {video_key.split('_')[0]}", expanded=True):
            col1, col2 = st.columns(2)
            
            # Original subtitles
            with col1:
                if st.download_button(
                    label="Download Original Subtitles",
                    data=video_data['original'],
                    file_name=f"{video_key.split('_')[0]}_original.{video_data['format']}",
                    mime="text/plain",
                    key=f"original_{video_key}",
                    on_click=handle_download,
                    args=(video_key, 'original')
                ):
                    pass  # Download handled by callback
                
                if st.session_state.get(f"original_{video_key}"):
                    st.success("✓ Original subtitles downloaded")

            # Translated subtitles
            with col2:
                if st.download_button(
                    label=f"Download {video_data['target_language']} Subtitles",
                    data=video_data['translated'],
                    file_name=f"{video_key.split('_')[0]}_{SUPPORTED_LANGUAGES[video_data['target_language']]}.{video_data['format']}",
                    mime="text/plain",
                    key=f"translated_{video_key}",
                    on_click=handle_download,
                    args=(video_key, 'translated')
                ):
                    pass  # Download handled by callback
                
                if st.session_state.get(f"translated_{video_key}"):
                    st.success(f"✓ {video_data['target_language']} subtitles downloaded")
        
        st.divider()

def main():
    st.title("Video Subtitling and Translation Tool")
    
    # Clear results button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Clear All Results"):
            st.session_state.processed_videos = {}
            st.session_state.download_status = {}
            st.rerun()
    
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
                    video_key = f"{video_file.name}_{i}"
                    
                    # Create an expander for each video
                    with st.expander(f"Video {i}: {video_file.name}", expanded=True):
                        st.write(f"Processing video {i}/{len(video_files)}")
                        progress_bar = st.progress(0)
                        
                        # Process the video
                        original_subtitles, translated_subtitles, error = process_single_video(
                            video_file, target_language, subtitle_format
                        )
                        
                        if error:
                            st.error(f"Error processing {video_file.name}: {error}")
                            continue
                        
                        # Store results in session state
                        st.session_state.processed_videos[video_key] = {
                            'original': original_subtitles,
                            'translated': translated_subtitles,
                            'target_language': target_language,
                            'format': subtitle_format
                        }
                        
                        progress_bar.progress(1.0)
                        st.success(f"✓ Processing completed")
                    
                    st.divider()
            
            # Display download section after processing
            display_download_section(video_files)
    
    # Always show download section for previously processed videos
    elif st.session_state.processed_videos:
        display_download_section(None)

if __name__ == "__main__":
    main()
