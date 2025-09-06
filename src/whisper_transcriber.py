#!/usr/bin/env python3
"""
Whisper-based transcription for videos without subtitles.
Supports Chinese and other languages.
"""

import whisper
import os
import subprocess
from pathlib import Path

class WhisperTranscriber:
    def __init__(self, model_size="base"):
        """Initialize Whisper model."""
        self.model = whisper.load_model(model_size)
    
    def transcribe_youtube_video(self, youtube_url, output_dir, language=None):
        """
        Download audio from YouTube and transcribe using Whisper.
        
        Args:
            youtube_url (str): YouTube video URL
            output_dir (str): Directory to save transcript
            language (str): Language code (e.g., 'zh', 'en') or None for auto-detect
            
        Returns:
            tuple: (success, transcript_file_path, transcript_text)
        """
        try:
            # Create temp directory for audio
            temp_dir = Path(output_dir) / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            # Download audio using yt-dlp
            audio_file = temp_dir / "audio.%(ext)s"
            cmd = [
                "yt-dlp",
                "-x",  # Extract audio
                "--audio-format", "wav",  # Convert to WAV for Whisper
                "-o", str(audio_file),
                youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return False, None, f"Failed to download audio: {result.stderr}"
            
            # Find the downloaded audio file
            audio_files = list(temp_dir.glob("audio.*"))
            if not audio_files:
                return False, None, "No audio file found after download"
            
            actual_audio_file = audio_files[0]
            
            # Transcribe using Whisper
            print(f"Transcribing audio with Whisper...")
            if language:
                result = self.model.transcribe(str(actual_audio_file), language=language)
            else:
                result = self.model.transcribe(str(actual_audio_file))
            
            # Get video title for filename
            title_cmd = ["yt-dlp", "--print", "title", youtube_url]
            title_result = subprocess.run(title_cmd, capture_output=True, text=True)
            
            if title_result.returncode == 0:
                title = title_result.stdout.strip()
                # Clean title for filename
                title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            else:
                title = "Unknown_Video"
            
            # Save transcript
            transcript_file = Path(output_dir) / f"{title}_whisper.txt"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(result["text"])
            
            # Clean up temp audio file
            actual_audio_file.unlink()
            temp_dir.rmdir()
            
            return True, str(transcript_file), result["text"]
            
        except Exception as e:
            return False, None, f"Transcription error: {e}"

def main():
    """Command line usage."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python whisper_transcriber.py <youtube_url> [language_code]")
        print("Example: python whisper_transcriber.py 'https://youtube.com/watch?v=...' zh")
        sys.exit(1)
    
    url = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else None
    
    transcriber = WhisperTranscriber()
    # Use absolute path
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    output_dir = os.path.join(base_dir, "transcript", "original")
    
    success, file_path, text = transcriber.transcribe_youtube_video(url, output_dir, language)
    
    if success:
        print(f"✅ Transcription completed: {file_path}")
        print(f"📝 Preview: {text[:200]}...")
    else:
        print(f"❌ Transcription failed: {text}")

if __name__ == "__main__":
    main()
