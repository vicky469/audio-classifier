#!/usr/bin/env python3
"""
Complete workflow orchestrator for YouTube to Notion transcript processing.
Handles the entire pipeline from YouTube URL to Notion page creation.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import webbrowser
import glob
from notion_integration import NotionIntegration
from transcript_processor import process_file

class TranscriptWorkflow:
    def __init__(self, base_dir=None):
        """Initialize the workflow with base directory."""
        if base_dir is None:
            base_dir = "/Users/wenqingli/Documents/repo/audio classifier"
        
        self.base_dir = Path(base_dir)
        self.original_dir = self.base_dir / "transcript" / "original"
        self.process_dir = self.base_dir / "transcript" / "process"
        self.clean_dir = self.base_dir / "transcript" / "clean"
        
        # Ensure directories exist
        for directory in [self.original_dir, self.process_dir, self.clean_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def run_complete_workflow(self, youtube_url, tags=None, open_notion=True):
        """
        Run the complete workflow from YouTube URL to Notion page.
        
        Args:
            youtube_url (str): YouTube video URL
            tags (list): Optional tags for the Notion page
            open_notion (bool): Whether to open the Notion page in browser
            
        Returns:
            dict: Results of each step
        """
        results = {
            'download': {'success': False},
            'process': {'success': False},
            'upload': {'success': False}
        }
        
        print("🚀 Starting YouTube to Notion workflow...")
        print(f"📺 URL: {youtube_url}")
        
        # Step 1: Download transcript from YouTube using shell script
        print("\n📥 Step 1: Downloading transcript from YouTube...")
        success, vtt_file, video_info = self._download_with_script(youtube_url)
        
        results['download'] = {
            'success': success,
            'file': vtt_file,
            'video_info': video_info
        }
        
        if not success:
            print("❌ Failed to download transcript")
            return results
        
        print(f"✅ Downloaded: {os.path.basename(vtt_file)}")
        
        # Step 2: Copy to process directory and clean transcript
        print("\n🔄 Step 2: Processing transcript...")
        
        # Copy to process directory
        process_file_path = self.process_dir / os.path.basename(vtt_file)
        shutil.copy2(vtt_file, process_file_path)
        print(f"📋 Copied to process directory: {process_file_path}")
        
        # Generate clean file path
        base_name = os.path.splitext(os.path.basename(vtt_file))[0]
        clean_file_path = self.clean_dir / f"{base_name}_clean.txt"
        
        # Process the transcript
        try:
            success = process_file(
                str(process_file_path),
                str(clean_file_path),
                words_per_chunk=100,
                words_per_line=15
            )
            
            results['process'] = {
                'success': success,
                'input_file': str(process_file_path),
                'output_file': str(clean_file_path)
            }
            
            if success:
                print(f"✅ Processed transcript: {clean_file_path}")
            else:
                print("❌ Failed to process transcript")
                return results
                
        except Exception as e:
            print(f"❌ Error processing transcript: {e}")
            results['process']['success'] = False
            return results
        
        # Step 3: Upload to Notion
        print("\n☁️  Step 3: Uploading to Notion...")
        
        try:
            notion = NotionIntegration()
            
            # Prepare tags
            if not tags:
                tags = ["transcript", "youtube", "video"]
                if video_info and video_info.get('uploader'):
                    tags.append(video_info['uploader'].lower().replace(' ', '-'))
            
            success, page_url, page_id = notion.upload_transcript(
                str(clean_file_path),
                video_info=video_info,
                tags=tags
            )
            
            results['upload'] = {
                'success': success,
                'page_url': page_url,
                'page_id': page_id
            }
            
            if success:
                print(f"✅ Uploaded to Notion: {page_url}")
                
                # Clean up process files after successful upload
                try:
                    if os.path.exists(process_file_path):
                        os.remove(process_file_path)
                        print(f"🗑️  Cleaned up process file: {os.path.basename(process_file_path)}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean up process file: {e}")
                
                # Open in browser if requested
                if open_notion and page_url:
                    print("🌐 Opening Notion page in browser...")
                    webbrowser.open(page_url)
            else:
                print("❌ Failed to upload to Notion")
                
        except Exception as e:
            print(f"❌ Error uploading to Notion: {e}")
            print("💡 Make sure you have set up your Notion integration and .env file")
            results['upload']['success'] = False
        
        # Summary
        print("\n📊 Workflow Summary:")
        print(f"   📥 Download: {'✅' if results['download']['success'] else '❌'}")
        print(f"   🔄 Process:  {'✅' if results['process']['success'] else '❌'}")
        print(f"   ☁️  Upload:   {'✅' if results['upload']['success'] else '❌'}")
        
        if all(step['success'] for step in results.values()):
            print("\n🎉 Workflow completed successfully!")
            if results['upload']['page_url']:
                print(f"🔗 Notion Page: {results['upload']['page_url']}")
        else:
            print("\n⚠️  Workflow completed with some failures")
        
        return results
    
    def _download_with_script(self, youtube_url):
        """Download transcript using the shell script."""
        try:
            script_path = self.base_dir / "scripts" / "download_transcript.sh"
            
            # Make script executable if not already
            os.chmod(script_path, 0o755)
            
            # Clear any existing VTT files to prevent reuse
            existing_vtt_files = glob.glob(str(self.original_dir / "*.vtt"))
            for old_file in existing_vtt_files:
                os.remove(old_file)
            
            # Run the download script
            result = subprocess.run(
                [str(script_path), youtube_url, str(self.original_dir)],
                capture_output=True,
                text=True,
                cwd=str(self.base_dir)
            )
            
            if result.returncode == 0:
                # Find the downloaded VTT file (should be the only one now)
                vtt_files = glob.glob(str(self.original_dir / "*.vtt"))
                if vtt_files:
                    # Should only be one file now
                    vtt_file = vtt_files[0]
                    
                    # Extract basic video info from filename
                    filename = os.path.basename(vtt_file)
                    title = os.path.splitext(filename)[0]
                    
                    video_info = {
                        'title': title,
                        'duration': 0,
                        'uploader': 'Unknown',
                        'upload_date': 'Unknown'
                    }
                    
                    return True, vtt_file, video_info
                else:
                    print("❌ No VTT file found after download")
                    return False, None, None
            else:
                print(f"❌ Download script failed: {result.stderr}")
                return False, None, None
                
        except Exception as e:
            print(f"❌ Error running download script: {e}")
            return False, None, None
    
    def process_existing_transcript(self, transcript_file, tags=None, open_notion=True):
        """
        Process an existing transcript file and upload to Notion.
        
        Args:
            transcript_file (str): Path to existing clean transcript file
            tags (list): Optional tags for the Notion page
            open_notion (bool): Whether to open the Notion page in browser
            
        Returns:
            dict: Upload results
        """
        print(f"📄 Processing existing transcript: {transcript_file}")
        
        try:
            notion = NotionIntegration()
            
            if not tags:
                tags = ["transcript", "notes"]
            
            success, page_url, page_id = notion.upload_transcript(
                transcript_file,
                tags=tags
            )
            
            if success:
                print(f"✅ Uploaded to Notion: {page_url}")
                
                if open_notion and page_url:
                    print("🌐 Opening Notion page in browser...")
                    webbrowser.open(page_url)
                    
                return {
                    'success': True,
                    'page_url': page_url,
                    'page_id': page_id
                }
            else:
                print("❌ Failed to upload to Notion")
                return {'success': False}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'success': False}

def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("🎯 YouTube to Notion Transcript Workflow")
        print("\nUsage:")
        print("  python workflow_orchestrator.py <youtube_url> [tags...]")
        print("  python workflow_orchestrator.py --existing <transcript_file> [tags...]")
        print("\nExamples:")
        print("  python workflow_orchestrator.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
        print("  python workflow_orchestrator.py 'https://youtu.be/dQw4w9WgXcQ' education blockchain")
        print("  python workflow_orchestrator.py --existing transcript.txt notes research")
        sys.exit(1)
    
    # Initialize workflow
    workflow = TranscriptWorkflow()
    
    # Check if processing existing file
    if sys.argv[1] == "--existing":
        if len(sys.argv) < 3:
            print("❌ Please provide a transcript file path")
            sys.exit(1)
        
        transcript_file = sys.argv[2]
        tags = sys.argv[3:] if len(sys.argv) > 3 else None
        
        if not os.path.exists(transcript_file):
            print(f"❌ File not found: {transcript_file}")
            sys.exit(1)
        
        results = workflow.process_existing_transcript(transcript_file, tags)
        
        if not results['success']:
            sys.exit(1)
    else:
        # Process YouTube URL
        youtube_url = sys.argv[1]
        tags = sys.argv[2:] if len(sys.argv) > 2 else None
        
        results = workflow.run_complete_workflow(youtube_url, tags)
        
        # Exit with error code if any step failed
        if not all(step['success'] for step in results.values()):
            sys.exit(1)

if __name__ == "__main__":
    main()
