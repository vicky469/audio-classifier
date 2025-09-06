#!/usr/bin/env python3
"""
Notion API integration for uploading cleaned transcripts to Notion workspace.
Creates pages with transcript content and metadata for note-taking.
"""

import os
import sys
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

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
        
    def create_page_in_database(self, title, content, video_info=None, tags=None):
        """
        Create a new page in the specified Notion database.
        
        Args:
            title (str): Page title
            content (str): Transcript content
            video_info (dict): Video metadata (title, uploader, etc.)
            tags (list): List of tags to add
            
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
                if video_info.get('author'):
                    properties["Author"] = {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": video_info['author']
                                }
                            }
                        ]
                    }
                
                if video_info.get('upload_date'):
                    properties["Created"] = {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": str(video_info['upload_date'])
                                }
                            }
                        ]
                    }
                
                if video_info.get('duration'):
                    # Convert duration to phone number format (just the number)
                    duration_min = str(video_info['duration'] // 60)
                    properties["Duration"] = {
                        "phone_number": duration_min
                    }
            
            # Add tags if provided - using URL format as that's what the database expects
            if tags:
                # For URL type, we'll just put the first tag as a URL or convert to text
                properties["Tags"] = {
                    "url": f"https://example.com/tags/{'-'.join(tags)}"
                }
            
            # Set default status
            properties["Status"] = {
                "status": {
                    "name": "Not started"
                }
            }
            
            # Create the page first without content (to avoid 100 block limit)
            if self.database_id:
                # Create in database
                response = self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties
                )
            else:
                # Create a page without database - need to find a parent page
                # First, let's try to get the user's pages to find a suitable parent
                try:
                    # Search for pages in the workspace
                    search_results = self.client.search(
                        query="",
                        filter={"property": "object", "value": "page"}
                    )
                    
                    if search_results["results"]:
                        # Use the first available page as parent
                        parent_page_id = search_results["results"][0]["id"]
                        response = self.client.pages.create(
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
                self.client.blocks.children.append(
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
                # Split long paragraphs if needed
                if len(paragraph) > 1800:  # Leave some buffer
                    # Split by sentences or at word boundaries
                    sentences = paragraph.split('. ')
                    current_block = ""
                    
                    for sentence in sentences:
                        if len(current_block + sentence) > 1800:
                            if current_block:
                                blocks.append(self._create_paragraph_block(current_block.strip()))
                            current_block = sentence + ". "
                        else:
                            current_block += sentence + ". "
                    
                    if current_block.strip():
                        blocks.append(self._create_paragraph_block(current_block.strip()))
                else:
                    blocks.append(self._create_paragraph_block(paragraph.strip()))
        
        # Add a divider and notes section
        blocks.extend([
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "My Notes"
                            }
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Add your notes and insights here..."
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
    
    def upload_transcript(self, transcript_file, video_info=None, tags=None):
        """
        Upload a cleaned transcript file to Notion.
        
        Args:
            transcript_file (str): Path to the cleaned transcript file
            video_info (dict): Video metadata
            tags (list): Tags to add to the page
            
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
            
            # Default tags
            if not tags:
                tags = ["transcript", "video", "notes"]
            
            return self.create_page_in_database(title, content, video_info, tags)
            
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
