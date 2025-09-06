#!/usr/bin/env python3
"""
Notion API integration for uploading cleaned transcripts to Notion workspace.
Creates pages with transcript content and metadata for note-taking.
"""

import os
import sys
import time
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

class NotionIntegration:
    def __init__(self, token=None, database_id=None):
        """Initialize Notion client with token and database ID."""
        self.token = token or os.getenv('NOTION_TOKEN')
        self.database_id = database_id or os.getenv('NOTION_DATABASE_ID')
        
        if not self.token:
            raise ValueError("Notion token not found. Please set NOTION_TOKEN in .env file")
        
        self.client = Client(auth=self.token)
        
    def _retry_api_call(self, func, *args, **kwargs):
        """
        Retry API calls with exponential backoff for timeout/connection errors.
        
        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the function call
        """
        max_retries = 3
        base_delay = 1  # Start with 1 second delay
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.Timeout, 
                    requests.exceptions.ConnectionError,
                    requests.exceptions.ReadTimeout,
                    Exception) as e:
                
                # Check if it's a timeout-related error
                error_msg = str(e).lower()
                is_timeout = any(keyword in error_msg for keyword in 
                               ['timeout', 'timed out', 'connection', 'read timeout'])
                
                if attempt < max_retries - 1 and is_timeout:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"⚠️  API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"🔄 Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    # Last attempt or non-timeout error, re-raise
                    raise e
    
    def create_page_in_database(self, title, content, video_info=None):
        """
        Create a new page in the specified Notion database.
        
        Args:
            title (str): Page title
            content (str): Transcript content
            video_info (dict): Video metadata (title, uploader, etc.)
            
        Returns:
            tuple: (success, page_url, page_id)
        """
        try:
            # Prepare properties for the database entry
            properties = {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Status": {
                    "status": {
                        "name": "Not started"
                    }
                }
            }
            
            # Add video metadata if available
            if video_info:
                # Use 'uploader' field for Author (channel name)
                if video_info.get('uploader'):
                    properties["Author"] = {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": video_info['uploader']
                                }
                            }
                        ]
                    }
                
                # Format upload_date for better display
                if video_info.get('upload_date') and video_info['upload_date'] != 'Unknown':
                    upload_date = video_info['upload_date']
                    # Format YYYYMMDD to YYYY-MM-DD if it's in that format
                    if len(upload_date) == 8 and upload_date.isdigit():
                        formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                    else:
                        formatted_date = str(upload_date)
                    
                    properties["Created"] = {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": formatted_date
                                }
                            }
                        ]
                    }
                
                # Convert duration from seconds to minutes for display
                if video_info.get('duration') and video_info['duration'] > 0:
                    duration_min = str(int(video_info['duration']) // 60)
                    properties["Duration"] = {
                        "phone_number": duration_min
                    }
                
                # Add view count if available
                if video_info.get('view_count') and video_info['view_count'] > 0:
                    view_count = f"{video_info['view_count']:,}"  # Format with commas
                    properties["Views"] = {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": view_count
                                }
                            }
                        ]
                    }
            
            
            # Add video URL if available
            if video_info and video_info.get('webpage_url'):
                properties["Video URL"] = {
                    "url": video_info['webpage_url']
                }
            
            # Set default status
            properties["Status"] = {
                "status": {
                    "name": "Not started"
                }
            }
            
            # Create the page first without content (to avoid 100 block limit)
            if self.database_id:
                # Create in database with retry
                response = self._retry_api_call(
                    self.client.pages.create,
                    parent={"database_id": self.database_id},
                    properties=properties
                )
            else:
                # Create a page without database - need to find a parent page
                # First, let's try to get the user's pages to find a suitable parent
                try:
                    # Search for pages in the workspace with retry
                    search_results = self._retry_api_call(
                        self.client.search,
                        query="",
                        filter={"property": "object", "value": "page"}
                    )
                    
                    if search_results["results"]:
                        # Use the first available page as parent
                        parent_page_id = search_results["results"][0]["id"]
                        response = self._retry_api_call(
                            self.client.pages.create,
                            parent={"type": "page_id", "page_id": parent_page_id},
                            properties={
                                "title": {
                                    "title": [
                                        {
                                            "type": "text",
                                            "text": {
                                                "content": title
                                            }
                                        }
                                    ]
                                }
                            }
                        )
                    else:
                        raise Exception("No suitable parent page found. Please set up a database or share an existing page with your integration.")
                except Exception as e:
                    raise Exception(f"Cannot create page without database. Please either:\n1. Set NOTION_DATABASE_ID in .env and share the database with your integration\n2. Share an existing page with your integration\nError: {e}")
            
            page_id = response["id"]
            page_url = response["url"]
            
            # Now add content in batches (Notion limit is 100 blocks per request)
            content_blocks = self._create_content_blocks(content)
            batch_size = 90  # Use 90 to be safe
            
            for i in range(0, len(content_blocks), batch_size):
                batch = content_blocks[i:i + batch_size]
                self._retry_api_call(
                    self.client.blocks.children.append,
                    block_id=page_id,
                    children=batch
                )
            
            print(f"✅ Created Notion page: {title}")
            print(f"🔗 URL: {page_url}")
            
            return True, page_url, page_id
            
        except Exception as e:
            print(f"❌ Error creating Notion page: {e}")
            return False, None, None
    
    def _create_content_blocks(self, content):
        """Convert transcript content into Notion blocks."""
        blocks = []
        
        # Add a heading
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Transcript Content"
                        }
                    }
                ]
            }
        })
        
        # Split content into paragraphs (Notion has a 2000 character limit per block)
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Split long paragraphs if needed (Notion limit is 2000 chars)
                text = paragraph.strip()
                if len(text) > 1900:  # Leave buffer for safety
                    # Split into chunks of 1900 characters at word boundaries
                    chunks = []
                    while len(text) > 1900:
                        # Find a good break point (space, comma, period, or Chinese punctuation)
                        break_point = 1900
                        for i in range(1900, max(1700, 0), -1):  # Look backwards for break point
                            if i < len(text) and text[i] in ' ,.。，！？\n':
                                break_point = i + 1
                                break
                        
                        chunks.append(text[:break_point].strip())
                        text = text[break_point:].strip()
                    
                    # Add remaining text
                    if text:
                        chunks.append(text)
                    
                    # Create blocks for each chunk
                    for chunk in chunks:
                        if chunk:
                            blocks.append(self._create_paragraph_block(chunk))
                else:
                    blocks.append(self._create_paragraph_block(text))
        
        # Add a divider and notes section
        blocks.extend([
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "📝 Add your notes here..."
                            }
                        }
                    ]
                }
            }
        ])
        
        return blocks
    
    def _create_paragraph_block(self, text):
        """Create a paragraph block for Notion."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": text
                        }
                    }
                ]
            }
        }
    
    def upload_transcript(self, transcript_file, video_info=None):
        """
        Upload a cleaned transcript file to Notion.
        
        Args:
            transcript_file (str): Path to the transcript file
            video_info (dict): Video metadata to add to the page
            
        Returns:
            tuple: (success, page_url, page_id)
        """
        try:
            # Read the transcript content
            with open(transcript_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generate title from filename or video info
            if video_info and video_info.get('title'):
                title = f"📺 {video_info['title']}"
            else:
                filename = os.path.basename(transcript_file)
                title = f"📺 {os.path.splitext(filename)[0].replace('_clean', '')}"
            
            return self.create_page_in_database(title, content, video_info)
            
        except Exception as e:
            print(f"❌ Error uploading transcript: {e}")
            return False, None, None

def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python notion_integration.py <transcript_file> [tags...]")
        print("Example: python notion_integration.py transcript.txt education blockchain")
        sys.exit(1)
    
    transcript_file = sys.argv[1]
    tags = sys.argv[2:] if len(sys.argv) > 2 else None
    
    # Initialize Notion integration
    try:
        notion = NotionIntegration()
        success, page_url, page_id = notion.upload_transcript(transcript_file, tags=tags)
        
        if success:
            print(f"🎉 Successfully uploaded to Notion!")
            print(f"🔗 Page URL: {page_url}")
        else:
            print("❌ Failed to upload to Notion")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📝 Setup Instructions:")
        print("1. Create a Notion integration at https://www.notion.so/my-integrations")
        print("2. Copy your integration token")
        print("3. Create a .env file with: NOTION_TOKEN=your_token_here")
        print("4. Optionally add: NOTION_DATABASE_ID=your_database_id")
        sys.exit(1)

if __name__ == "__main__":
    main()
