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
    
    # Create a blob URL for subtitles
    vtt_base64 = base64.b64encode(subtitles_vtt.encode()).decode()
    
    return f'''
        <video width="100%" controls>
            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
            <track 
                label="Subtitles" 
                kind="subtitles" 
                srclang="en" 
                src="data:text/vtt;base64,{vtt_base64}" 
                default
            >
            Your browser does not support the video tag.
        </video>
        <script>
            const video = document.querySelector('video');
            const track = video.querySelector('track');
            track.mode = 'showing';
            video.textTracks[0].mode = 'showing';
        </script>
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
        
        # Create original subtitles
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
                translated_segments = video_data['segments'].copy()
                
                if video_data['format'] == 'srt':
                    try:
                        lines = [line for line in video_data['translated'].strip().split('\n\n') if line.strip()]
                        translated_segments = []
                        for line in lines:
                            parts = line.strip().split('\n')
                            if len(parts) >= 3:
                                timestamp_line = parts[1].strip()
                                if ' --> ' in timestamp_line:
                                    start_time, end_time = timestamp_line.split(' --> ')
                                    # Parse timestamps with improved error handling
                                    start_time = srt_timestamp_to_seconds(start_time.strip())
                                    end_time = srt_timestamp_to_seconds(end_time.strip())
                                    if start_time >= 0 and end_time > start_time:
                                        text = '\n'.join(parts[2:]).strip()
                                        if text:
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

def main():
    # Set page config with basic SEO
    st.set_page_config(
        page_title="Video Subtitling and Translation Tool",
        page_icon="🎬",
        layout="wide",
        menu_items={
            'Get Help': 'https://subtool-trkn.replit.app',
            'Report a bug': 'https://subtool-trkn.replit.app',
            'About': '© 2024 trhacknon - A powerful video subtitling and translation tool'
        }
    )

    # Add SEO and social meta tags using components.html
    st.components.v1.html('''
        <meta name="description" content="Process videos, generate transcriptions, and create translations using OpenAI's Whisper and GPT-4 APIs">
        <meta name="author" content="trhacknon">
        <meta property="og:type" content="website">
        <meta property="og:url" content="https://subtool-trkn.replit.app">
        <meta property="og:title" content="Video Subtitling and Translation Tool">
        <meta property="og:description" content="Automatic video subtitling and translation with OpenAI">
        <meta property="og:image" content="https://subtool-trkn.replit.app/icon.png">
        <meta property="twitter:card" content="summary_large_image">
        <meta property="twitter:url" content="https://subtool-trkn.replit.app">
        <meta property="twitter:title" content="Video Subtitling and Translation Tool">
        <meta property="twitter:description" content="Automatic video subtitling and translation with OpenAI">
        <meta property="twitter:image" content="https://subtool-trkn.replit.app/icon.png">
    ''', height=0)

    st.title("Video Subtitling and Translation Tool")
    
    st.write("Upload videos to generate subtitles and translations")
    
    # File uploader for video files
    video_files = st.file_uploader(
        "Choose video files",
        type=SUPPORTED_VIDEO_FORMATS,
        accept_multiple_files=True,
        help=f"Maximum file size: {MediaService.MAX_FILE_SIZE_MB}MB"
    )
    
    if video_files:
        # Target language selection
        target_language = st.selectbox(
            "Select target language",
            options=list(SUPPORTED_LANGUAGES.keys()),
            index=0
        )
        
        # Subtitle format selection
        subtitle_format = st.selectbox(
            "Select subtitle format",
            options=SUPPORTED_SUBTITLE_FORMATS,
            index=0,
            help="Choose the format for generated subtitles"
        )
        
        # Process button
        if st.button("Process Videos"):
            with st.spinner("Processing videos..."):
                for video_file in video_files:
                    if video_file is None:
                        continue
                        
                    # Create a unique key for this video
                    video_key = f"{video_file.name.split('.')[0]}_{int(time.time())}"
                    
                    # Process video and get subtitles
                    original_subtitles, translated_subtitles, segments, temp_video_path, error = process_single_video(
                        video_file, target_language, subtitle_format
                    )
                    
                    if error:
                        st.error(f"Error processing {video_file.name}: {error}")
                        continue
                    
                    # Store results in session state
                    st.session_state.processed_videos[video_key] = {
                        'original': original_subtitles,
                        'translated': translated_subtitles,
                        'segments': segments,
                        'video_path': temp_video_path,
                        'format': subtitle_format,
                        'target_language': target_language
                    }
                
                st.success("Processing complete!")
            
            # Display download section
            display_download_section(video_files)

if __name__ == "__main__":
    main()
