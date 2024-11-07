import os
from openai import OpenAI
from typing import Dict, Any

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper API
        """
        with open(audio_file_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        return response

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
