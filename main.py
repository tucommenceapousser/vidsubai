import streamlit as st
import os
import tempfile
import io
import zipfile
import base64
from services.openai_service import OpenAIService
from services.media_service import MediaService
from services.subtitle_service import SubtitleService
from services.timing_service import TimingService
from utils.constants import SUPPORTED_LANGUAGES, SUPPORTED_VIDEO_FORMATS, SUPPORTED_SUBTITLE_FORMATS
import time
from moviepy.editor import VideoFileClip

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

def srt_timestamp_to_seconds(timestamp):
    """Convert SRT timestamp to seconds"""
    try:
        # Split hours, minutes, seconds
        parts = timestamp.split(':')
        if len(parts) != 3:
            return 0.0
        
        hours = int(parts[0])
        minutes = int(parts[1])
        # Handle seconds and milliseconds
        seconds_parts = parts[2].replace(',', '.').split('.')
        seconds = float(seconds_parts[0])
        milliseconds = float('0.' + seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        return hours * 3600 + minutes * 60 + seconds + milliseconds
    except (ValueError, IndexError):
        return 0.0

def get_video_html(video_path, subtitles_vtt):
    video_base64 = ""
    with open(video_path, "rb") as f:
        video_base64 = base64.b64encode(f.read()).decode()
    
    # Ensure VTT content starts with WEBVTT
    if not subtitles_vtt.startswith('WEBVTT'):
        subtitles_vtt = 'WEBVTT\n\n' + subtitles_vtt
    
    # Create a blob URL for subtitles
    vtt_base64 = base64.b64encode(subtitles_vtt.encode()).decode()
    
    return f'''
        <div class="video-container">
            <video id="previewVideo" width="100%" controls crossorigin="anonymous">
                <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                <track 
                    label="Subtitles"
                    kind="subtitles" 
                    srclang="en" 
                    src="data:text/vtt;base64,{vtt_base64}"
                    default
                />
            </video>
            <style>
                .video-container {{
                    position: relative;
                    width: 100%;
                    margin: 20px 0;
                }}
                video::cue {{
                    background-color: rgba(0,0,0,0.7);
                    color: white;
                    font-size: 1.2em;
                }}
            </style>
            <script>
                // Function to handle track loading
                function initializeSubtitles(video) {{
                    if (!video) return;
                    
                    // Force enable the first text track
                    const track = video.textTracks[0];
                    if (track) {{
                        // Disable all tracks first
                        Array.from(video.textTracks).forEach(t => t.mode = 'disabled');
                        // Enable our track
                        track.mode = 'showing';
                    }}
                }}

                // Initialize when DOM is loaded
                document.addEventListener('DOMContentLoaded', () => {{
                    const video = document.getElementById('previewVideo');
                    if (video) {{
                        // Initialize when metadata is loaded
                        video.addEventListener('loadedmetadata', () => initializeSubtitles(video));
                        
                        // Backup initialization after a short delay
                        setTimeout(() => initializeSubtitles(video), 1000);
                        
                        // Handle track loading
                        video.addEventListener('addtrack', () => initializeSubtitles(video));
                    }}
                }});
            </script>
        </div>
    '''

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
            return None, None, None, None, f"File {video_file.name} ({file_size_mb:.1f}MB) exceeds the maximum limit of {MediaService.MAX_FILE_SIZE_MB}MB."

        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_video_path = os.path.join(temp_dir, video_file.name)
        with open(temp_video_path, "wb") as f:
            f.write(video_file.getbuffer())

        # Extract audio
        audio_path = media_service.extract_audio(temp_video_path)

        # Get video FPS for SUB format
        video_fps = 23.976  # Default FPS
        if subtitle_format == 'sub':
            try:
                with VideoFileClip(temp_video_path) as video:
                    video_fps = video.fps
            except:
                pass

        # Transcribe audio
        original_segments = openai_service.transcribe_audio(audio_path)
        
        # Create original language subtitles
        original_subtitles = subtitle_service.create_subtitles(
            original_segments,
            subtitle_format,
            fps=video_fps
        )

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
        translated_subtitles = subtitle_service.create_subtitles(
            translated_segments,
            subtitle_format,
            fps=video_fps
        )

        return original_subtitles, translated_subtitles, original_segments, temp_video_path, None

    except Exception as e:
        return None, None, None, None, str(e)
    finally:
        if temp_dir and 'temp_video_path' not in locals():
            media_service.cleanup_temp_files([temp_dir])

def display_download_section(video_files):
    """Display download section with video preview and subtitle downloads"""
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
            # Video preview with subtitles
            if video_data.get('video_path'):
                st.markdown("##### Video Preview with Subtitles")
                # Always convert to VTT for video preview
                preview_subtitles = subtitle_service.create_vtt(video_data['segments'])
                
                st.markdown(
                    get_video_html(video_data['video_path'], preview_subtitles),
                    unsafe_allow_html=True
                )
            
            st.markdown("##### Text Preview")
            # Subtitle text preview
            pcol1, pcol2 = st.columns(2)
            with pcol1:
                st.markdown("**Original Segments:**")
                for i, segment in enumerate(video_data['segments']):
                    st.markdown(f"**{i+1}. [{segment['start']:.1f}s - {segment['end']:.1f}s]**")
                    st.text(segment['text'])
                    st.divider()
            
            with pcol2:
                st.markdown(f"**{video_data['target_language']} Segments:**")
                translated_segments = video_data['segments'].copy()  # Use a copy of original segments for timing
                if video_data['format'] == 'srt':
                    # Parse translated subtitles back into segments with improved error handling
                    try:
                        lines = [line for line in video_data['translated'].strip().split('\n\n') if line.strip()]
                        translated_segments = []
                        for line in lines:
                            parts = line.strip().split('\n')
                            if len(parts) >= 3:  # Valid SRT entry has index, timestamp, and text
                                timestamp_line = parts[1].strip()
                                if ' --> ' in timestamp_line:
                                    start_time, end_time = timestamp_line.split(' --> ')
                                    # Clean and parse timestamps
                                    start_time = srt_timestamp_to_seconds(start_time.strip())
                                    end_time = srt_timestamp_to_seconds(end_time.strip())
                                    if start_time >= 0 and end_time > start_time:  # Valid timestamps
                                        text = '\n'.join(parts[2:]).strip()
                                        if text:  # Only add if there's actual text content
                                            translated_segments.append({
                                                'start': start_time,
                                                'end': end_time,
                                                'text': text
                                            })
                    except Exception as e:
                        st.error(f"Error parsing SRT timestamps: {str(e)}")
                        st.info("Using original segment timings as fallback")
                
                for i, segment in enumerate(translated_segments):
                    st.markdown(f"**{i+1}. [{segment['start']:.1f}s - {segment['end']:.1f}s]**")
                    st.text(segment['text'])
                    st.divider()
        
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
            label="Download All Subtitle Files",
            data=zip_buffer.getvalue(),
            file_name="subtitles.zip",
            mime="application/zip",
            key="batch_download"
        )
        
        # Clear selected files after creating zip
        st.session_state.selected_files = []

def main():
    st.title("Video Subtitling and Translation Tool")
    
    # Add custom CSS for modern styling
    st.markdown('''
        <style>
            /* Main container styles */
            .stApp {
                background: linear-gradient(145deg, #111111, #1a1a1a);
            }
            
            /* Headers */
            h1, h2, h3 {
                color: #00ffbb !important;
                text-shadow: 0 0 10px rgba(0, 255, 187, 0.3);
            }
            
            /* Buttons */
            .stButton > button {
                background-color: transparent;
                border: 2px solid #00ffbb;
                color: #00ffbb;
                border-radius: 5px;
                transition: all 0.3s ease;
            }
            .stButton > button:hover {
                background-color: #00ffbb;
                color: #111111;
                box-shadow: 0 0 15px rgba(0, 255, 187, 0.5);
            }
            
            /* Input fields */
            .stTextInput > div > div > input,
            .stNumberInput > div > div > input {
                border: 2px solid #444;
                background-color: #2b2b2b;
                color: white;
                border-radius: 5px;
            }
            .stTextInput > div > div > input:focus,
            .stNumberInput > div > div > input:focus {
                border-color: #00ffbb;
                box-shadow: 0 0 10px rgba(0, 255, 187, 0.3);
            }
            
            /* Expander */
            .streamlit-expanderHeader {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
            }
            .streamlit-expanderHeader:hover {
                border-color: #00ffbb;
            }
            
            /* File uploader */
            .stFileUploader > div {
                background-color: #2b2b2b;
                border: 2px dashed #444;
                border-radius: 5px;
            }
            .stFileUploader > div:hover {
                border-color: #00ffbb;
            }
            
            /* Select boxes */
            .stSelectbox > div > div {
                background-color: #2b2b2b;
                border: 2px solid #444;
                border-radius: 5px;
            }
            .stSelectbox > div > div:hover {
                border-color: #00ffbb;
            }
        </style>
    ''', unsafe_allow_html=True)
    
    # Clear results button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Clear All Results"):
            # Clean up temporary video files
            for video_data in st.session_state.processed_videos.values():
                if video_data.get('video_path'):
                    try:
                        os.remove(video_data['video_path'])
                    except:
                        pass
            
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
                        original_subtitles, translated_subtitles, original_segments, temp_video_path, error = process_single_video(
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
                            'format': subtitle_format,
                            'target_language': target_language,
                            'video_path': temp_video_path
                        }
                        
                        progress_bar.progress(1.0)
                        st.success(f"✓ Processing completed")

            # Display download section
            display_download_section(video_files)

if __name__ == "__main__":
    main()
