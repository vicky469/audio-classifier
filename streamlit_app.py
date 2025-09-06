#!/usr/bin/env python3
"""
Streamlit web interface for YouTube to Notion transcript processing.
Provides a user-friendly GUI for the complete workflow.
"""

import streamlit as st
import sys
import os
from pathlib import Path
import threading
import time

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from workflow_orchestrator import TranscriptWorkflow

# Page configuration
st.set_page_config(
    page_title="YouTube to Notion Processor",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = None
if 'progress_messages' not in st.session_state:
    st.session_state.progress_messages = []

def reset_state():
    """Reset processing state for new workflow."""
    st.session_state.processing = False
    st.session_state.results = None
    st.session_state.current_step = None
    st.session_state.progress_messages = []

def add_progress_message(message):
    """Add a progress message to the session state."""
    st.session_state.progress_messages.append(message)

def process_video_workflow(youtube_url):
    """Run the complete workflow with proper progress tracking."""
    try:
        st.session_state.processing = True
        st.session_state.current_step = "initializing"
        st.session_state.progress_messages = ["🚀 Starting YouTube to Notion workflow..."]
        
        # Initialize workflow
        workflow = TranscriptWorkflow()
        
        # Step 1: Download
        st.session_state.current_step = "downloading"
        st.session_state.progress_messages.append("📥 Downloading transcript from YouTube...")
        
        # Get download results first
        success, raw_file, video_info = workflow._download_with_script(youtube_url)
        
        results = {
            'download': {
                'success': success,
                'file': raw_file,
                'video_info': video_info
            },
            'process': {'success': False},
            'upload': {'success': False}
        }
        
        if not success:
            st.session_state.progress_messages.append("❌ Failed to download transcript")
            st.session_state.results = results
            st.session_state.processing = False
            st.session_state.current_step = "error"
            return
        
        st.session_state.progress_messages.append(f"✅ Downloaded: {os.path.basename(raw_file)}")
        
        # Step 2: Process
        st.session_state.current_step = "processing"
        st.session_state.progress_messages.append("🔄 Processing transcript...")
        
        from transcript_processor import process_file
        clean_file_path = workflow.clean_dir / f"{os.path.splitext(os.path.basename(raw_file))[0]}_clean.txt"
        process_success = process_file(str(raw_file), str(clean_file_path))
        
        results['process'] = {
            'success': process_success,
            'clean_file': str(clean_file_path) if process_success else None
        }
        
        if not process_success:
            st.session_state.progress_messages.append("❌ Failed to process transcript")
            st.session_state.results = results
            st.session_state.processing = False
            st.session_state.current_step = "error"
            return
        
        st.session_state.progress_messages.append(f"✅ Processed transcript: {clean_file_path.name}")
        
        # Step 3: Upload
        st.session_state.current_step = "uploading"
        st.session_state.progress_messages.append("☁️ Uploading to Notion...")
        
        from notion_integration import NotionIntegration
        notion = NotionIntegration()
        upload_success, page_url, page_id = notion.upload_transcript(
            str(clean_file_path),
            video_info=video_info
        )
        
        results['upload'] = {
            'success': upload_success,
            'page_url': page_url,
            'page_id': page_id
        }
        
        if upload_success:
            st.session_state.progress_messages.append(f"✅ Uploaded to Notion: {page_url}")
            # Clean up raw file
            if os.path.exists(raw_file):
                os.remove(raw_file)
                st.session_state.progress_messages.append(f"🗑️ Cleaned up raw file")
        else:
            st.session_state.progress_messages.append("❌ Failed to upload to Notion")
        
        # Store final results
        st.session_state.results = results
        st.session_state.processing = False
        st.session_state.current_step = "completed"
        
        if all(step['success'] for step in results.values()):
            st.session_state.progress_messages.append("🎉 Workflow completed successfully!")
        else:
            st.session_state.progress_messages.append("⚠️ Workflow completed with some failures")
            
    except Exception as e:
        st.session_state.processing = False
        st.session_state.current_step = "error"
        st.session_state.progress_messages.append(f"❌ Error: {str(e)}")
        st.session_state.results = {'error': str(e)}

def main():
    """Main Streamlit application."""
    
    # Header
    st.title("🎯 YouTube to Notion Transcript Processor")
    st.markdown("Transform YouTube videos into organized Notion pages with clean transcripts")
    
    # Input section
    st.markdown("---")
    st.subheader("📺 YouTube Video Input")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste the YouTube video URL you want to process",
            label_visibility="collapsed"
        )
    
    with col2:
        process_button = st.button(
            "Process Video",
            type="primary",
            disabled=st.session_state.processing or not youtube_url,
            use_container_width=True
        )
    
    # Process button logic
    if process_button and youtube_url and not st.session_state.processing:
        reset_state()
        # Run workflow directly (synchronous for better progress tracking)
        process_video_workflow(youtube_url)
        st.rerun()
    
    # Progress section
    if st.session_state.processing or st.session_state.results:
        st.markdown("---")
        st.subheader("📊 Processing Status")
        
        # Progress indicators
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.session_state.current_step in ["downloading", "processing", "uploading", "completed"]:
                st.success("📥 Download Complete")
            elif st.session_state.current_step == "downloading":
                st.info("📥 Downloading...")
            else:
                st.empty()
        
        with col2:
            if st.session_state.current_step in ["processing", "uploading", "completed"]:
                st.success("🔄 Processing Complete")
            elif st.session_state.current_step == "processing":
                st.info("🔄 Processing...")
            else:
                st.empty()
        
        with col3:
            if st.session_state.current_step == "completed":
                st.success("☁️ Upload Complete")
            elif st.session_state.current_step == "uploading":
                st.info("☁️ Uploading...")
            else:
                st.empty()
        
        # Progress messages
        if st.session_state.progress_messages:
            st.markdown("**Progress Log:**")
            for message in st.session_state.progress_messages:
                st.text(message)
    
    # Results section
    if st.session_state.results and not st.session_state.processing:
        st.markdown("---")
        st.subheader("✅ Results")
        
        results = st.session_state.results
        
        if 'error' in results:
            st.error(f"❌ Error occurred: {results['error']}")
            st.info("💡 Make sure you have set up your Notion integration and .env file")
        else:
            # Success/failure summary
            success_count = sum(1 for step in results.values() if step.get('success', False))
            total_steps = len(results)
            
            if success_count == total_steps:
                st.success("🎉 All steps completed successfully!")
                
                # Show results
                if results.get('upload', {}).get('success') and results['upload'].get('page_url'):
                    st.markdown("### 🔗 Notion Page Created")
                    notion_url = results['upload']['page_url']
                    st.markdown(f"[Open in Notion]({notion_url})")
                    
                    if st.button("🌐 Open Notion Page", type="secondary"):
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={notion_url}">', 
                                  unsafe_allow_html=True)
                
                # Show file info
                if results.get('process', {}).get('clean_file'):
                    clean_file = results['process']['clean_file']
                    st.markdown(f"### 📄 Clean Transcript")
                    st.text(f"Saved to: {os.path.basename(clean_file)}")
                
            else:
                st.warning(f"⚠️ {success_count}/{total_steps} steps completed successfully")
                
                # Show step details
                for step_name, step_data in results.items():
                    if step_data.get('success'):
                        st.success(f"✅ {step_name.title()}: Success")
                    else:
                        st.error(f"❌ {step_name.title()}: Failed")
        
        # Process another video button
        st.markdown("---")
        if st.button("🔄 Process Another Video", type="secondary"):
            reset_state()
            st.rerun()
    
    # Sidebar with info
    with st.sidebar:
        st.markdown("### ℹ️ About")
        st.markdown("""
        This tool processes YouTube videos through a complete workflow:
        
        1. **📥 Download** - Extract transcript from YouTube
        2. **🔄 Process** - Clean and format the transcript  
        3. **☁️ Upload** - Create organized Notion page
        
        ### 🔧 Requirements
        - Valid YouTube URL
        - Notion integration configured
        - Environment variables set in `.env`
        """)
        
        st.markdown("### 🚀 Quick Start")
        st.markdown("""
        1. Paste YouTube URL
        2. Click 'Process Video'
        3. Wait for completion
        4. Open your new Notion page!
        """)

if __name__ == "__main__":
    main()
