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

# Extract metadata once and store in memory
echo "📊 Extracting video metadata..."
METADATA=$(yt-dlp --dump-json --no-warnings "$YOUTUBE_URL" 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$METADATA" ]; then
    echo "❌ Failed to fetch video metadata"
    exit 1
fi

# Parse metadata for language detection
echo "🔍 Analyzing metadata for language detection..."
SUBTITLES=$(echo "$METADATA" | jq -r '.subtitles | keys[]?' 2>/dev/null | grep -E '^(zh|zh-.*)')
CHANNEL=$(echo "$METADATA" | jq -r '.channel // .uploader // ""' 2>/dev/null)

# Detect language
if [ -n "$SUBTITLES" ]; then
    DETECTED_LANG="zh"
    echo "🎯 Found Chinese subtitles, detected language: Chinese"
elif echo "$CHANNEL" | grep -qE '[一-龯]'; then
    DETECTED_LANG="zh"
    echo "🎯 Detected Chinese channel name: $CHANNEL, detected language: Chinese"
else
    DETECTED_LANG="en"
    echo "🎯 No Chinese indicators found, detected language: English"
fi

# Try multiple methods to bypass YouTube restrictions

# Method 1: Standard download with detected language priority
echo "🔄 Method 1: Trying standard download (prioritizing $DETECTED_LANG)..."

# Then download subtitles
yt-dlp --write-auto-subs --sub-langs "en,zh,zh-CN,zh-TW" --sub-format "vtt" --skip-download \
    --output "$TRANSCRIPT_DIR/%(title)s.%(ext)s" "$YOUTUBE_URL" 2>/dev/null

# Check if any VTT files were actually created
if ls "$TRANSCRIPT_DIR"/*.vtt 1> /dev/null 2>&1; then
    # Save metadata to match the transcript filename
    VTT_FILE=$(ls "$TRANSCRIPT_DIR"/*.vtt | head -1)
    BASE_NAME=$(basename "$VTT_FILE" .vtt)
    echo "$METADATA" > "$TRANSCRIPT_DIR/${BASE_NAME}.json"
    echo "📊 Saved metadata: ${BASE_NAME}.json"
    echo "✅ Downloaded transcript (Method 1: Standard)"
    exit 0
else
    echo "⚠️  Method 1 failed - no subtitles available"
fi

# Method 2: Fallback to Whisper transcription
echo "🔄 Method 4: No subtitles found, trying Whisper transcription..."

cd "$BASE_DIR"

# Use already detected language from metadata
echo "🎯 Using detected language: $DETECTED_LANG"

# Run Whisper transcriber
if python src/whisper_transcriber.py "$YOUTUBE_URL" "$DETECTED_LANG"; then
    echo "✅ Downloaded transcript (Method 4: Whisper transcription)"
    exit 0
else
    echo "❌ Whisper transcription failed"
fi

echo "❌ No transcript available (all methods failed)"
exit 1
