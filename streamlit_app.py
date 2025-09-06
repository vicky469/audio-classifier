#!/usr/bin/env python3
"""
Streamlit web interface for YouTube to Notion transcript processing.
Provides a user-friendly GUI for the complete workflow.
"""

import streamlit as st
import sys
import os
from pathlib import Path

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
if 'clear_input' not in st.session_state:
    st.session_state.clear_input = False

def reset_state():
    """Reset processing state for new workflow."""
    st.session_state.processing = False
    st.session_state.results = None
    st.session_state.current_step = None
    st.session_state.progress_messages = []
    st.session_state.clear_input = True
    st.session_state.youtube_url_value = ""
    st.session_state.previous_url = ""
    # Delete the widget key to force recreation
    if 'youtube_input' in st.session_state:
        del st.session_state.youtube_input

def add_progress_message(message):
    """Add a progress message to the session state."""
    st.session_state.progress_messages.append(message)

def process_video_workflow(youtube_url):
    """Run the complete workflow with proper progress tracking."""
    try:
        # Check if processing was stopped
        if not st.session_state.get('processing', False):
            return
            
        st.session_state.processing = True
        st.session_state.current_step = "initializing"
        st.session_state.progress_messages = ["🚀 Starting YouTube to Notion workflow..."]
        
        # Initialize workflow
        workflow = TranscriptWorkflow()
        
        # Step 1: Download
        if not st.session_state.get('processing', False):
            return
            
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
        if not st.session_state.get('processing', False):
            return
            
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
        if not st.session_state.get('processing', False):
            return
            
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
        print(f"⏹️ Processing interrupted: {str(e)}")
        st.session_state.processing = False
        st.session_state.current_step = None
        st.session_state.progress_messages.append("⏹️ Processing stopped by user")
        st.session_state.results = None

def main():
    """Main Streamlit application."""
    
    # Header
    st.title("🎯 YouTube to Notion Transcript Processor")
    st.markdown("Transform YouTube videos into organized Notion pages with clean transcripts")
    st.markdown("---")
    
    # Input section
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Use a dynamic key to force widget recreation when clearing
        widget_key = f"youtube_input_{st.session_state.get('input_counter', 0)}"
        
        # Clear input value if reset was requested
        if st.session_state.clear_input:
            input_value = ""
            st.session_state.clear_input = False  # Reset the flag
            # Increment counter to create new widget
            st.session_state.input_counter = st.session_state.get('input_counter', 0) + 1
            widget_key = f"youtube_input_{st.session_state.input_counter}"
        else:
            input_value = st.session_state.get('youtube_url_value', '')
            
        youtube_url = st.text_input(
            "YouTube URL",
            value=input_value,
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste the YouTube video URL you want to process, then press Enter",
            label_visibility="collapsed",
            key=widget_key,
            disabled=st.session_state.processing
        )
        
        # Store the current input value
        st.session_state.youtube_url_value = youtube_url
    
    with col2:
        # Button styling and state
        button_disabled = st.session_state.processing
        button_text = "Processing..." if st.session_state.processing else "Process Video"
        
        process_button = st.button(
            button_text,
            disabled=button_disabled,
            use_container_width=True,
            help="Click to start processing the YouTube video" if not button_disabled else "Processing in progress..."
        )
        
    
    # Check if Enter was pressed (input value changed and not empty)
    enter_pressed = False
    if youtube_url and youtube_url != st.session_state.get('previous_url', '') and not st.session_state.processing:
        enter_pressed = True
        st.session_state.previous_url = youtube_url
    
    # Process button logic or Enter key
    if (process_button or enter_pressed) and youtube_url and not st.session_state.processing:
        # Set processing state immediately to disable UI elements
        st.session_state.processing = True
        st.session_state.current_step = "initializing"
        st.session_state.progress_messages = ["🚀 Starting YouTube to Notion workflow..."]
        # Force immediate UI update to show disabled state
        st.rerun()
    
    # Show stop button when processing
    if st.session_state.processing:
        st.markdown("---")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("⏹️ Stop", key="stop_processing", type="primary"):
                st.session_state.processing = False
                st.session_state.current_step = None
                st.session_state.progress_messages.append("⏹️ Processing stopped by user")
                st.rerun()
        with col2:
            st.info("🔄 Processing in progress... Click the Stop button to cancel.")
    
    # Run workflow step by step with UI updates
    if st.session_state.processing and st.session_state.current_step == "initializing":
        # Start downloading
        st.session_state.current_step = "downloading"
        st.session_state.progress_messages = ["🚀 Starting YouTube to Notion workflow...", "📥 Downloading transcript from YouTube..."]
        st.rerun()
    
    elif st.session_state.processing and st.session_state.current_step == "downloading":
        # Run download step
        try:
            workflow = TranscriptWorkflow()
            success, raw_file, video_info = workflow._download_with_script(youtube_url)
            
            if success:
                st.session_state.download_results = {
                    'success': success,
                    'file': raw_file,
                    'video_info': video_info
                }
                st.session_state.current_step = "processing"
                st.session_state.progress_messages.append(f"✅ Downloaded: {os.path.basename(raw_file)}")
                st.session_state.progress_messages.append("🔄 Processing transcript...")
            else:
                st.session_state.download_results = {'success': False}
                st.session_state.results = {
                    'download': {'success': False},
                    'process': {'success': False},
                    'upload': {'success': False}
                }
                st.session_state.processing = False
                st.session_state.current_step = "error"
                st.session_state.progress_messages.append("❌ Failed to download transcript")
        except Exception as e:
            st.session_state.download_results = {'success': False}
            st.session_state.results = {
                'download': {'success': False},
                'process': {'success': False},
                'upload': {'success': False}
            }
            st.session_state.processing = False
            st.session_state.current_step = "error"
            st.session_state.progress_messages.append(f"❌ Error: {str(e)}")
        st.rerun()
    
    elif st.session_state.processing and st.session_state.current_step == "processing":
        # Run processing step
        try:
            from transcript_processor import process_file
            raw_file = st.session_state.download_results['file']
            workflow = TranscriptWorkflow()
            clean_file_path = workflow.clean_dir / f"{os.path.splitext(os.path.basename(raw_file))[0]}_clean.txt"
            process_success = process_file(str(raw_file), str(clean_file_path))
            
            if process_success:
                st.session_state.process_results = {
                    'success': process_success,
                    'clean_file': str(clean_file_path)
                }
                st.session_state.current_step = "uploading"
                st.session_state.progress_messages.append(f"✅ Processed transcript: {clean_file_path.name}")
                st.session_state.progress_messages.append("☁️ Uploading to Notion...")
            else:
                st.session_state.process_results = {'success': False}
                st.session_state.results = {
                    'download': st.session_state.download_results,
                    'process': {'success': False},
                    'upload': {'success': False}
                }
                st.session_state.processing = False
                st.session_state.current_step = "error"
                st.session_state.progress_messages.append("❌ Failed to process transcript")
        except Exception as e:
            st.session_state.process_results = {'success': False}
            st.session_state.results = {
                'download': st.session_state.download_results,
                'process': {'success': False},
                'upload': {'success': False}
            }
            st.session_state.processing = False
            st.session_state.current_step = "error"
            st.session_state.progress_messages.append(f"❌ Error: {str(e)}")
        st.rerun()
    
    elif st.session_state.processing and st.session_state.current_step == "uploading":
        # Run upload step
        try:
            from notion_integration import NotionIntegration
            notion = NotionIntegration()
            clean_file_path = st.session_state.process_results['clean_file']
            video_info = st.session_state.download_results['video_info']
            
            upload_success, page_url, page_id = notion.upload_transcript(
                clean_file_path,
                video_info=video_info
            )
            
            # Store final results
            st.session_state.results = {
                'download': st.session_state.download_results,
                'process': st.session_state.process_results,
                'upload': {
                    'success': upload_success,
                    'page_url': page_url,
                    'page_id': page_id
                }
            }
            
            st.session_state.processing = False
            st.session_state.current_step = "completed"
            
            if upload_success:
                st.session_state.progress_messages.append(f"✅ Uploaded to Notion: {page_url}")
                st.session_state.progress_messages.append("🎉 Workflow completed successfully!")
            else:
                st.session_state.progress_messages.append("❌ Failed to upload to Notion")
                st.session_state.progress_messages.append("⚠️ Workflow completed with some failures")
        except Exception as e:
            st.session_state.results = {
                'download': st.session_state.download_results,
                'process': st.session_state.process_results,
                'upload': {'success': False}
            }
            st.session_state.processing = False
            st.session_state.current_step = "error"
            st.session_state.progress_messages.append(f"❌ Error: {str(e)}")
        st.rerun()
    
    
    # Progress section
    if st.session_state.processing or st.session_state.results:
        if not st.session_state.processing:
            st.markdown("---")
        st.subheader("📊 Processing Status")
        
        # Progress indicators
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.session_state.current_step == "downloading":
                st.info("📥 Downloading...")
            elif st.session_state.current_step == "error" and not st.session_state.get('download_results', {}).get('success', False):
                st.error("📥 Download Failed")
            elif st.session_state.current_step in ["processing", "uploading", "completed"] or (st.session_state.current_step == "error" and st.session_state.get('download_results', {}).get('success', False)):
                st.success("📥 Download Complete")
        
        with col2:
            if st.session_state.current_step == "processing":
                st.info("🔄 Processing...")
            elif st.session_state.current_step == "error" and st.session_state.get('download_results', {}).get('success', False) and not st.session_state.get('process_results', {}).get('success', False):
                st.error("🔄 Processing Failed")
            elif st.session_state.current_step in ["uploading", "completed"] or (st.session_state.current_step == "error" and st.session_state.get('process_results', {}).get('success', False)):
                st.success("🔄 Processing Complete")
        
        with col3:
            if st.session_state.current_step == "uploading":
                st.info("☁️ Uploading...")
            elif st.session_state.current_step == "error" and st.session_state.get('process_results', {}).get('success', False):
                st.error("☁️ Upload Failed")
            elif st.session_state.current_step == "completed":
                st.success("☁️ Upload Complete")
        
        # Progress messages
        if st.session_state.progress_messages:
            st.markdown("**Progress Log:**")
            for message in st.session_state.progress_messages:
                st.text(message)
    
    # Results section
    if st.session_state.results and not st.session_state.processing:
        st.markdown("---")
        
        results = st.session_state.results
        
        if 'error' in results:
            st.subheader("❌ Results")
            st.error(f"❌ Error occurred: {results['error']}")
            st.info("💡 Make sure you have set up your Notion integration and .env file")
        else:
            # Success/failure summary
            success_count = sum(1 for step in results.values() if step.get('success', False))
            total_steps = len(results)
            
            if success_count == total_steps:
                st.subheader("✅ Results")
                st.success("🎉 All steps completed successfully!")
                
                # Show results ONLY when ALL steps succeed
                if results.get('upload', {}).get('success') and results['upload'].get('page_url'):
                    st.markdown("### 🔗 Notion Page Created")
                    notion_url = results['upload']['page_url']
                    st.markdown(f"[Open in Notion]({notion_url})")
                    
                    if st.button("🌐 Open Notion Page", type="primary"):
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={notion_url}">', 
                                  unsafe_allow_html=True)
                
                # Show file info ONLY when processing succeeded
                if results.get('process', {}).get('clean_file'):
                    clean_file = results['process']['clean_file']
                    st.markdown(f"### 📄 Clean Transcript")
                    st.text(f"Saved to: {os.path.basename(clean_file)}")
                
            else:
                st.subheader("❌ Results")
                # When ANY step fails, do NOT show success content
                st.warning(f"⚠️ {success_count}/{total_steps} steps completed successfully")
        
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
