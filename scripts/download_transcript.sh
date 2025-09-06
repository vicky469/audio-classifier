#!/bin/bash

# Simple YouTube transcript downloader
# Usage: ./download_transcript.sh <youtube_url>

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
TRANSCRIPT_DIR="$BASE_DIR/transcript/original"

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
# Method 1: Use cookies and different user agent
if yt-dlp --write-auto-subs --sub-langs "en" --sub-format "vtt" --skip-download \
    --cookies-from-browser chrome \
    --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    --output "$TRANSCRIPT_DIR/%(title)s.%(ext)s" "$YOUTUBE_URL" 2>/dev/null; then
    
    echo "✅ Downloaded English transcript"
    exit 0

# Method 2: Try with different extractor args
elif yt-dlp --write-auto-subs --sub-langs "en" --sub-format "vtt" --skip-download \
    --extractor-args "youtube:player_client=android" \
    --output "$TRANSCRIPT_DIR/%(title)s.%(ext)s" "$YOUTUBE_URL" 2>/dev/null; then
    
    echo "✅ Downloaded English transcript (Android client)"
    exit 0

# Method 3: Basic attempt without special options
elif yt-dlp --write-subs --sub-langs "en" --sub-format "vtt" --skip-download \
    --output "$TRANSCRIPT_DIR/%(title)s.%(ext)s" "$YOUTUBE_URL" 2>/dev/null; then
    
    echo "✅ Downloaded transcript"
    exit 0
    
else
    echo "❌ No transcript available or video is restricted"
    exit 1
fi
