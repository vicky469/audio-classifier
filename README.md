# YouTube to Notion Transcript Workflow Setup

This automated workflow allows you to:

1. Download transcripts from YouTube videos
2. Clean and format the transcripts
3. Upload them to Notion for note-taking
4. Automatically open the Notion page in your browser

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd "/Users/wenqingli/Documents/repo/audio classifier"
pip install -r requirements.txt
```

### 2. Set Up Notion Integration

#### Create a Notion Integration:

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Give it a name (e.g., "Transcript Processor")
4. Select your workspace
5. Copy the "Internal Integration Token"

#### Set Up Your Database (Optional but Recommended):

1. Create a new database in Notion with these properties:

   - **Title** (Title)
   - **Status** (Select: "Ready for Notes", "In Progress", "Complete")
   - **Author** (Text)
   - **Duration (min)** (Number)
   - **Tags** (Multi-select)
   - **Created** (Date)

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

NOTION_DATABASE_ID=your_database_id_here  # Optional

```

### 3. Run the Workflow

#### Complete Workflow (YouTube → Notion):

```bash
python src/workflow_orchestrator.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### With Custom Tags:

```bash
python src/workflow_orchestrator.py "https://www.youtube.com/watch?v=VIDEO_ID" education blockchain crypto
```

#### Process Existing Clean Transcript:

```bash
python src/workflow_orchestrator.py --existing "transcript/clean/your_file_clean.txt" notes research
```

## 📁 File Structure

```
audio classifier/
├── scripts/
│   ├── download_transcript.sh      # YouTube transcript downloader
├── src/
│   ├── workflow_orchestrator.py    # Main workflow script
│   ├── notion_integration.py       # Notion API integration
│   └── transcript_processor.py     # Transcript cleaner/formatter
├── transcript/
│   ├── original/                   # Raw VTT files from YouTube
│   ├── process/                    # Intermediate processing files
│   └── clean/                      # Cleaned, formatted transcripts
├── requirements.txt                # Python dependencies
├── .env                           # API keys and configuration
```

## 🎯 Workflow Steps

1. **Download**: Extracts transcript from YouTube video using `youtube-transcript-api`
2. **Process**: Copies VTT file to process directory and runs transcript cleaner
3. **Clean**: Removes timestamps, repetitions, and formats into readable chunks
4. **Upload**: Creates a Notion page with the cleaned transcript and metadata
5. **Open**: Automatically opens the Notion page in your browser for note-taking

## 🔍 Features

- **Smart Repetition Removal**: Detects and removes repetitive phrases automatically
- **Proper Formatting**: 100-word chunks with 15 words per line for readability
- **Rich Metadata**: Includes video title, author, duration, and upload date (TODO)
- **Automatic Tagging**: Adds relevant tags based on content and video info
- **Browser Integration**: Opens Notion page automatically for immediate note-taking
- **Error Handling**: Comprehensive error messages and fallback options

## 🛠 Troubleshooting

### "No transcript available"

- Some videos don't have transcripts
- Try videos with auto-generated captions
- Check if the video is public and accessible

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
# Complete workflow with a YouTube video
python src/workflow_orchestrator.py "https://www.youtube.com/watch?v=JJqjTxaVSGw&ab_channel=WhenShiftHappens"

# Process existing transcript file
python src/workflow_orchestrator.py --existing "transcript/clean/my_transcript_clean.txt" research notes

# Just download transcript (no Notion upload)
python src/youtube_downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```
