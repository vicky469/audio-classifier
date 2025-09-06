# YouTube to Notion Transcript Workflow Setup

This automated workflow allows you to:

1. Download transcripts from YouTube videos with rich metadata extraction
2. Clean and format the transcripts with language-specific formatting
3. Upload them to Notion with comprehensive video metadata
4. Automatically open the Notion page in your browser for immediate note-taking

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ".../repo/audio classifier"
pip install -r requirements.txt
```

### 2. Set Up Notion Integration

#### Create a Notion Integration:

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Give it a name (e.g., "Transcript Processor")
4. Select your workspace
5. Copy the "Internal Integration Token"

#### Set Up Your Database:

1. Create a new database in Notion with these properties:

   - **Title** (Title)
   - **Status** (Status: "Not started", "In progress", "Complete")
   - **Author** (Rich Text) - for channel/uploader name
   - **Created** (Rich Text) - for upload date
   - **Duration** (Phone Number) - for video length in minutes
   - **Views** (Rich Text) - for view count
   - **Video URL** (URL) - for YouTube video link

2. Share the database with your integration:
   - Click "Share" on your database
   - Add your integration
   - Copy the database ID from the URL

#### Create Environment File:

```bash
cp .env.example .env
```

Edit `.env` file:

```
NOTION_TOKEN=your_integration_token_here
NOTION_DATABASE_ID=your_database_id_here
```

### 3. Run the Workflow

#### Complete Workflow (YouTube → Notion):

```bash
python src/workflow_orchestrator.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### Process Existing Clean Transcript:

```bash
python src/workflow_orchestrator.py --existing "transcript/clean/your_file_clean.txt"
```

## 📁 File Structure

```
audio classifier/
├── scripts/
│   └── download_transcript.sh      # YouTube transcript downloader
├── src/
│   ├── workflow_orchestrator.py    # Main workflow script
│   ├── notion_integration.py       # Notion API integration
│   ├── transcript_processor.py     # Transcript cleaner/formatter
│   └── whisper_transcriber.py      # Whisper audio transcription
├── transcript/
│   ├── raw/                        # Raw downloaded files (VTT/TXT)
│   ├── failed/                     # Files that failed processing
│   └── clean/                      # Cleaned, formatted transcripts
├── requirements.txt                # Python dependencies
└── .env                           # API keys and configuration
```

## 🎯 Workflow Steps

1. **Download**: Extracts transcripts and rich metadata using yt-dlp:
   - Downloads subtitles (VTT format)
   - Extracts comprehensive video metadata (title, channel, upload date, duration, view count, URL)
   - Saves metadata as JSON file alongside transcript
2. **Process**: Cleans and formats transcript with language-specific rules:
   - English: 15 words per line, 100 words per chunk
   - Chinese: 50 characters per line, 500 words per chunk
   - Removes repetitive phrases and timestamps
3. **Upload**: Creates Notion page with rich metadata:
   - Video title, channel name, upload date, duration, view count, YouTube URL
   - Formatted transcript content in organized chunks
4. **Cleanup**: Removes raw files after successful upload
5. **Open**: Automatically opens the Notion page in your browser

## 🔍 Features

- **Rich Metadata Extraction**: Captures comprehensive video information (title, channel, upload date, duration, view count, URL)
- **Efficient API Usage**: Single metadata extraction using yt-dlp --dump-json (no redundant API calls)
- **Language Support**: Optimized formatting for English and Chinese videos
- **Smart Formatting**: 
  - English: 15 words per line, 100 words per chunk
  - Chinese: 50 characters per line, 500 words per chunk
- **Smart Repetition Removal**: Detects and removes repetitive phrases automatically
- **Comprehensive Notion Integration**: Creates pages with rich metadata fields
- **Automatic Cleanup**: Removes raw files after successful processing
- **Simplified Directory Structure**: Direct processing from raw to clean (no intermediate directories)
- **Browser Integration**: Opens Notion page automatically for immediate note-taking

## 🛠 Troubleshooting

### "No transcript available"

- The workflow uses yt-dlp to download subtitles
- If download fails, the video may not have subtitles or may be private
- Check if the video is public and has subtitles available
- For videos without subtitles, consider using the Whisper transcriber separately

### "Notion token not found"

- Make sure `.env` file exists with `NOTION_TOKEN`
- Verify your integration token is correct
- Ensure the integration has access to your workspace

### "Permission denied" errors

- Make sure your Notion integration has access to the target database/page
- Check that the database ID is correct

### Import errors

- Run `pip install -r requirements.txt`
- Make sure you're in the correct directory

## 📝 Example Usage

```bash
# Complete workflow with a YouTube video (downloads transcript + metadata)
python src/workflow_orchestrator.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Process existing transcript file
python src/workflow_orchestrator.py --existing "transcript/clean/my_transcript_clean.txt"
```

## 🆕 Recent Updates

- **Enhanced Metadata Extraction**: Now captures comprehensive video metadata using yt-dlp
- **Rich Notion Integration**: Uploads video metadata to structured Notion database fields
- **Simplified Workflow**: Removed custom tags (managed manually in Notion)
- **Improved Efficiency**: Single API call for both transcript and metadata
- **Better Formatting**: Optimized Chinese text formatting with character-based line breaks
