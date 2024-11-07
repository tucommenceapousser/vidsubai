import streamlit as st
import os
import tempfile
import io
import zipfile
from services.openai_service import OpenAIService
from services.media_service import MediaService
from services.subtitle_service import SubtitleService
from services.timing_service import TimingService
from utils.constants import SUPPORTED_LANGUAGES, SUPPORTED_VIDEO_FORMATS, SUPPORTED_SUBTITLE_FORMATS
import time

# Initialize services
openai_service = OpenAIService()
media_service = MediaService()
subtitle_service = SubtitleService()
timing_service = TimingService()

# Initialize session states
if 'processed_videos' not in st.session_state:
    st.session_state.processed_videos = {}
if 'current_segments' not in st.session_state:
    st.session_state.current_segments = {}

def create_download_component(key, subtitle_data, file_name, language=None):
    return st.download_button(
        label=f"Download {language if language else 'Original'} Subtitles",
        data=subtitle_data,
        file_name=file_name,
        mime="text/plain",
        key=f"download_{key}",
        use_container_width=True
    )

def update_subtitles(video_key, segments, subtitle_format):
    """Update subtitles after timing adjustments"""
    if subtitle_format == 'srt':
        return subtitle_service.create_srt(segments)
    return subtitle_service.create_vtt(segments)

def display_timing_adjustment(video_key, video_data):
    """Display timing adjustment controls for a video"""
    st.markdown("#### Timing Adjustment")
    
    # Get current segments
    if video_key not in st.session_state.current_segments:
        # Parse existing subtitles back into segments
        st.session_state.current_segments[video_key] = video_data.get('segments', [])
    
    segments = st.session_state.current_segments[video_key]
    
    # Global offset adjustment
    col1, col2 = st.columns(2)
    with col1:
        offset = st.number_input(
            "Global time offset (seconds)",
            value=0.0,
            step=0.1,
            key=f"offset_{video_key}"
        )
        if st.button("Apply Offset", key=f"apply_offset_{video_key}"):
            adjusted_segments = timing_service.adjust_global_offset(segments, offset)
            st.session_state.current_segments[video_key] = adjusted_segments
            
            # Update subtitles
            video_data['segments'] = adjusted_segments
            video_data['original'] = update_subtitles(video_key, adjusted_segments, video_data['format'])
            st.success("Global offset applied successfully!")
            st.rerun()
    
    with col2:
        scale = st.number_input(
            "Duration scale factor",
            value=1.0,
            min_value=0.1,
            max_value=5.0,
            step=0.1,
            key=f"scale_{video_key}"
        )
        if st.button("Apply Scaling", key=f"apply_scale_{video_key}"):
            adjusted_segments = timing_service.adjust_duration_scale(segments, scale)
            st.session_state.current_segments[video_key] = adjusted_segments
            
            # Update subtitles
            video_data['segments'] = adjusted_segments
            video_data['original'] = update_subtitles(video_key, adjusted_segments, video_data['format'])
            st.success("Duration scaling applied successfully!")
            st.rerun()
    
    # Individual segment adjustment
    st.markdown("##### Adjust Individual Segments")
    for i, segment in enumerate(segments):
        with st.expander(f"Segment {i+1}: {segment['text'][:50]}..."):
            col1, col2 = st.columns(2)
            with col1:
                new_start = st.number_input(
                    "Start time (seconds)",
                    value=float(segment['start']),
                    step=0.1,
                    key=f"start_{video_key}_{i}"
                )
            with col2:
                new_end = st.number_input(
                    "End time (seconds)",
                    value=float(segment['end']),
                    step=0.1,
                    key=f"end_{video_key}_{i}"
                )
            
            if st.button("Update Timing", key=f"update_timing_{video_key}_{i}"):
                adjusted_segments = timing_service.adjust_segment_timing(
                    segments, i, new_start, new_end
                )
                st.session_state.current_segments[video_key] = adjusted_segments
                
                # Update subtitles
                video_data['segments'] = adjusted_segments
                video_data['original'] = update_subtitles(video_key, adjusted_segments, video_data['format'])
                st.success(f"Segment {i+1} timing updated successfully!")
                st.rerun()

def process_single_video(video_file, target_language, subtitle_format):
    """Process a single video file and return subtitles"""
    temp_dir = None
    try:
        # Check file size
        file_size_mb = len(video_file.getbuffer()) / (1024 * 1024)
        if file_size_mb > MediaService.MAX_FILE_SIZE_MB:
            return None, None, None, f"File {video_file.name} ({file_size_mb:.1f}MB) exceeds the maximum limit of {MediaService.MAX_FILE_SIZE_MB}MB."

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

        return original_subtitles, translated_subtitles, original_segments, None

    except Exception as e:
        return None, None, None, str(e)
    finally:
        # Cleanup
        if temp_dir:
            media_service.cleanup_temp_files([temp_dir])

def display_download_section(video_files):
    if not st.session_state.processed_videos:
        return

    st.markdown("### Download Processed Subtitles")
    
    for video_key, video_data in st.session_state.processed_videos.items():
        st.markdown(f"#### {video_key.split('_')[0]}")
        
        # Add timing adjustment section
        display_timing_adjustment(video_key, video_data)
        
        # Use columns for layout
        col1, col2 = st.columns(2)
        
        # Original subtitles download
        with col1:
            create_download_component(
                f"orig_{video_key}",
                video_data['original'],
                f"{video_key.split('_')[0]}_original.{video_data['format']}"
            )
        
        # Translated subtitles download
        with col2:
            create_download_component(
                f"trans_{video_key}",
                video_data['translated'],
                f"{video_key.split('_')[0]}_{video_data['target_language']}.{video_data['format']}",
                video_data['target_language']
            )
        
        # Preview section using expander
        with st.expander("Show Preview", expanded=False):
            pcol1, pcol2 = st.columns(2)
            with pcol1:
                st.text_area(
                    "Original subtitles:",
                    value=video_data['original'][:500] + "...",
                    height=150,
                    key=f"preview_orig_{video_key}",
                    disabled=True
                )
            with pcol2:
                st.text_area(
                    f"{video_data['target_language']} subtitles:",
                    value=video_data['translated'][:500] + "...",
                    height=150,
                    key=f"preview_trans_{video_key}",
                    disabled=True
                )
        
        st.divider()

        # Add to selected_files for batch downloading
        if 'selected_files' not in st.session_state:
            st.session_state.selected_files = []
            
        st.session_state.selected_files.extend([
            {
                'filename': f"{video_key.split('_')[0]}_original.{video_data['format']}",
                'data': video_data['original']
            },
            {
                'filename': f"{video_key.split('_')[0]}_{video_data['target_language']}.{video_data['format']}",
                'data': video_data['translated']
            }
        ])

    # Add batch download button
    if st.session_state.selected_files:
        # Create zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in st.session_state.selected_files:
                zip_file.writestr(file['filename'], file['data'])
        
        # Download button for zip file
        st.download_button(
            label=f"Download All Subtitle Files",
            data=zip_buffer.getvalue(),
            file_name="subtitles.zip",
            mime="application/zip",
            key="batch_download"
        )
        
        # Clear selected files after creating zip
        st.session_state.selected_files = []

def main():
    st.title("Video Subtitling and Translation Tool")
    
    # Clear results button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Clear All Results"):
            st.session_state.processed_videos = {}
            st.session_state.current_segments = {}
            if 'selected_files' in st.session_state:
                st.session_state.selected_files = []
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
                        original_subtitles, translated_subtitles, original_segments, error = process_single_video(
                            video_file, target_language, subtitle_format
                        )
                        
                        if error:
                            st.error(f"Error processing {video_file.name}: {error}")
                            continue
                        
                        # Store results in session state
                        st.session_state.processed_videos[video_key] = {
                            'original': original_subtitles,
                            'translated': translated_subtitles,
                            'segments': original_segments,
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
