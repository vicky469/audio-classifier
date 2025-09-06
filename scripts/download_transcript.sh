#!/bin/bash

# Simple YouTube transcript downloader
# Usage: ./download_transcript.sh <youtube_url>

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
TRANSCRIPT_DIR="$BASE_DIR/transcript/raw"

# Check if URL is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <youtube_url>"
    exit 1
fi

YOUTUBE_URL="$1"

# Create directory
mkdir -p "$TRANSCRIPT_DIR"

echo "Downloading transcript from: $YOUTUBE_URL"

# Try multiple methods to bypass YouTube restrictions

# Method 1: Standard download with English and Chinese
echo "🔄 Method 1: Trying standard download (English/Chinese)..."

# First, extract metadata
echo "📊 Extracting video metadata..."
yt-dlp --dump-json --no-warnings "$YOUTUBE_URL" > "$TRANSCRIPT_DIR/temp_metadata.json" 2>/dev/null

# Then download subtitles
yt-dlp --write-auto-subs --sub-langs "en,zh,zh-CN,zh-TW" --sub-format "vtt" --skip-download \
    --output "$TRANSCRIPT_DIR/%(title)s.%(ext)s" "$YOUTUBE_URL" 2>/dev/null

# Check if any VTT files were actually created
if ls "$TRANSCRIPT_DIR"/*.vtt 1> /dev/null 2>&1; then
    # Move metadata file to match the transcript filename
    if [ -f "$TRANSCRIPT_DIR/temp_metadata.json" ]; then
        VTT_FILE=$(ls "$TRANSCRIPT_DIR"/*.vtt | head -1)
        BASE_NAME=$(basename "$VTT_FILE" .vtt)
        mv "$TRANSCRIPT_DIR/temp_metadata.json" "$TRANSCRIPT_DIR/${BASE_NAME}.json"
        echo "📊 Saved metadata: ${BASE_NAME}.json"
    fi
    echo "✅ Downloaded transcript (Method 1: Standard)"
    exit 0
else
    # Clean up temp metadata if subtitle download failed
    rm -f "$TRANSCRIPT_DIR/temp_metadata.json"
    echo "⚠️  Method 1 failed - no subtitles available"
fi

# Method 2: Fallback to Whisper transcription
echo "🔄 Method 4: No subtitles found, trying Whisper transcription..."

# Check if we're in the right directory structure
if [ -f "$BASE_DIR/src/whisper_transcriber.py" ]; then
    cd "$BASE_DIR"
    
    # Try to detect language (assume Chinese if channel has Chinese characters)
    if echo "$YOUTUBE_URL" | grep -q "%E"; then
        LANG="zh"
        echo "🎯 Detected Chinese channel, using Chinese language model"
    else
        LANG="en"
        echo "🎯 Using English language model"
    fi
    
    # Run Whisper transcriber
    if python src/whisper_transcriber.py "$YOUTUBE_URL" "$LANG"; then
        echo "✅ Downloaded transcript (Method 4: Whisper transcription)"
        exit 0
    else
        echo "❌ Whisper transcription failed"
    fi
else
    echo "❌ Whisper transcriber not found at $BASE_DIR/src/whisper_transcriber.py"
fi

echo "❌ No transcript available (all methods failed)"
exit 1
