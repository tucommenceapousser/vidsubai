import os
from openai import OpenAI
from typing import Dict, Any, List

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def transcribe_audio(self, audio_file_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe audio using Whisper API and format the response into segments
        """
        with open(audio_file_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            
            # Split the text into sentences and create time-aligned segments
            # Since the new API doesn't provide detailed timing, we'll estimate it
            text = response.text
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            
            # Create segments with estimated timing (3 seconds per sentence)
            segments = []
            current_time = 0
            for sentence in sentences:
                # Estimate 3 seconds per sentence
                segment_duration = 3
                segments.append({
                    'start': current_time,
                    'end': current_time + segment_duration,
                    'text': sentence + '.'
                })
                current_time += segment_duration
            
            return segments

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate text using GPT-4
        """
        prompt = f"Translate the following text to {target_language}:\n\n{text}"
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
