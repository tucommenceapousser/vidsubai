# Video Subtitling and Translation Tool 😈

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40.0-FF4B4B.svg)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-Whisper%20%26%20GPT--4-00A67E.svg)](https://openai.com)

## Online Demo By TRHACKNON
[![online demo](https://img.shields.io/badge/Streamlit-DEMO-FF4B4B.svg)](https://subtool-trkn.replit.app)

A powerful video subtitling and audio translation platform that leverages OpenAI's Whisper and GPT-4 APIs to automatically generate and translate subtitles. This tool supports multiple subtitle formats and languages, making it perfect for content creators and translators.

<details>
<summary>🌟 Features</summary>

- **Automatic Transcription**: Uses OpenAI's Whisper API for accurate speech-to-text conversion
- **Multi-language Translation**: Supports translation to 20+ languages including:
  - English, Spanish, French, German, Italian
  - Portuguese, Chinese, Japanese, Korean
  - Russian, Arabic, Hindi, Dutch, Polish
  - Turkish, Vietnamese, Thai, Swedish
  - Danish, Finnish
- **Multiple Subtitle Formats**:
  - SRT (SubRip)
  - WebVTT
  - ASS/SSA
  - MicroDVD SUB
- **Batch Processing**: Process multiple videos simultaneously
- **Timing Adjustment Tools**:
  - Global offset adjustment
  - Duration scaling
  - Individual segment timing
- **Preview Functionality**:
  - Integrated video player with subtitle overlay
  - Side-by-side text comparison
- **SEO Optimized**: Semantic HTML structure with meta tags
</details>

<details>
<summary>🚀 Getting Started</summary>

### System Requirements

- Python 3.11 or higher
- 2GB RAM minimum
- 1GB free disk space
- Modern web browser (Chrome, Firefox, Safari)

### Prerequisites

- Python 3.11+
- OpenAI API key
- Streamlit account (for deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vidsubai.git
cd vidsubai
```

2. Install dependencies:
```bash
pip install streamlit openai moviepy
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY='your-api-key'
```

### Local Development

Run the application locally:
```bash
streamlit run main.py
```

The application will be available at `http://localhost:5000`

### Configuration

Create `.streamlit/config.toml`:
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000

[theme]
primaryColor = "#00ffbb"
backgroundColor = "#111111"
secondaryBackgroundColor = "#2b2b2b"
textColor = "#ffffff"
font = "sans serif"
```
</details>

<details>
<summary>📖 Usage Guide</summary>

### Single Video Processing

1. Upload your video file (supported formats: MP4, MOV, AVI, MKV)
2. Select target language for translation
3. Choose desired subtitle format
4. Click "Process Video"
5. Download generated subtitles in original and translated languages

Example:
```python
# Upload video and process
video_file = "example.mp4"
target_language = "Spanish"
subtitle_format = "srt"

# Generated subtitles will be available for download
original_subs = "example_original.srt"
translated_subs = "example_spanish.srt"
```

### Batch Processing

1. Upload multiple video files
2. Configure language and format settings
3. Process all videos simultaneously
4. Download subtitles individually or as a zip file

Example:
```python
# Process multiple videos
video_files = ["video1.mp4", "video2.mp4", "video3.mp4"]
target_language = "French"
subtitle_format = "vtt"

# Results will be available as individual files or zip archive
download_zip = "batch_subtitles.zip"
```

### Timing Adjustments

1. Use global offset to shift all subtitles
2. Apply duration scaling to adjust timing
3. Fine-tune individual segment timings
4. Preview changes in real-time

Example:
```python
# Adjust timing
offset_seconds = 2.5  # Delay subtitles by 2.5 seconds
scale_factor = 1.1   # Stretch duration by 10%
```
</details>

<details>
<summary>🔧 API Documentation</summary>

### OpenAI Service

```python
class OpenAIService:
    def transcribe_audio(self, audio_file_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe audio using Whisper API
        
        Args:
            audio_file_path (str): Path to audio file
            
        Returns:
            List[Dict]: List of transcribed segments with timing
        """
        
    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate text using GPT-4
        
        Args:
            text (str): Text to translate
            target_language (str): Target language code
            
        Returns:
            str: Translated text
        """
```

### Subtitle Service

```python
class SubtitleService:
    def create_subtitles(self, segments: List[dict], format: str, fps: float = 23.976) -> str:
        """
        Create subtitles in specified format
        
        Args:
            segments (List[dict]): List of subtitle segments
            format (str): Subtitle format (srt, vtt, ass, sub)
            fps (float): Frames per second for SUB format
            
        Returns:
            str: Formatted subtitle content
        """
```

### Media Service

```python
class MediaService:
    def extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            str: Path to extracted audio file
        """
```

### Timing Service

```python
class TimingService:
    def adjust_global_offset(self, segments: List[Dict[str, Any]], offset_seconds: float) -> List[Dict[str, Any]]:
        """
        Adjust all subtitle timings
        
        Args:
            segments (List[Dict]): List of subtitle segments
            offset_seconds (float): Time offset in seconds
            
        Returns:
            List[Dict]: Adjusted segments
        """
```
</details>

<details>
<summary>📦 Deployment</summary>

### Deploying on Replit

1. Create a new Replit project
2. Upload project files or connect to GitHub
3. Set environment variables:
   - Add `OPENAI_API_KEY` in Replit Secrets
4. Install dependencies:
   ```bash
   python -m pip install streamlit openai moviepy
   ```
5. Configure `.streamlit/config.toml`:
   ```toml
   [server]
   headless = true
   address = "0.0.0.0"
   port = 5000
   ```
6. Run the application
7. Configure custom domain (optional)

The application will be automatically deployed and accessible via Replit's hosting.
</details>

<details>
<summary>❓ Troubleshooting</summary>

### Common Issues

1. **OpenAI API Error**
   ```
   Solution: Verify API key is set correctly in environment variables
   ```

2. **Video Processing Failed**
   ```
   Solution: Check video file format and size (max 25MB)
   ```

3. **Subtitle Timing Issues**
   ```
   Solution: Use timing adjustment tools in the interface
   ```

4. **Memory Errors**
   ```
   Solution: Process smaller video files or reduce batch size
   ```

### Performance Optimization

1. Use compressed video files
2. Process videos in smaller batches
3. Clear browser cache regularly
4. Use recommended video formats (MP4)
</details>

<details>
<summary>🤝 Contributing</summary>

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add unit tests for new features
- Update documentation as needed
- Use type hints and docstrings
- Include examples for new features
</details>

<details>
<summary>📄 License</summary>

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 trhacknon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
</details>

<details>
<summary>🙏 Acknowledgments</summary>

- OpenAI for Whisper and GPT-4 APIs
- Streamlit for the web framework
- MoviePy for video processing
- All contributors and users of this tool
</details>

---
Made with ❤️ by [trhacknon](https://github.com/tucommenceapousser)
