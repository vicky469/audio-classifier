#!/usr/bin/env python3
"""
Simple transcript processor that:
1. Cleans VTT files by removing timestamps and formatting
2. Removes audio cues like [Music], [Applause], etc.
3. Divides text into chunks of 100 words
4. Formats each line with max 15 words and adds line breaks
"""

import os
import re
import glob
import sys
import string

def remove_audio_cues(text):
    """Remove audio cues and sound descriptions from text."""
    # Remove audio cues and sound descriptions
    text = re.sub(r'\[.*?\]', '', text)  # Remove [Music], [Applause], etc.
    text = re.sub(r'\(.*?\)', '', text)  # Remove (music), (applause), etc.
    
    # Remove common audio cue words that might appear without brackets
    text = re.sub(r'\b(music|applause|laughter|cheering|background noise)\b', '', text, flags=re.IGNORECASE)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def detect_language(text):
    """Detect if text is primarily Chinese or English."""
    # Count Chinese characters (CJK Unified Ideographs)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # Count English words (sequences of Latin letters)
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    
    # If more than 30% Chinese characters, consider it Chinese
    total_chars = len(text.replace(' ', ''))
    if total_chars > 0 and chinese_chars / total_chars > 0.3:
        return 'chinese'
    return 'english'

def clean_vtt_content(content):
    """Extract and clean text from VTT content."""
    # Remove WebVTT header
    content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
    
    # Extract text content from the VTT file
    # This regex pattern matches timestamp lines
    timestamp_pattern = re.compile(r'\d+:\d+:\d+\.\d+ --> \d+:\d+:\d+\.\d+.*?$', re.MULTILINE)
    
    # Split content by timestamp lines
    segments = timestamp_pattern.split(content)
    segments = [s.strip() for s in segments if s.strip()]
    
    # Process each segment to extract clean text
    clean_texts = []
    for segment in segments:
        # Remove alignment and position info
        segment = re.sub(r'^align:.*?$', '', segment, flags=re.MULTILINE)
        segment = re.sub(r'^position:.*?$', '', segment, flags=re.MULTILINE)
        
        # Remove formatting codes
        segment = re.sub(r'<\d+:\d+:\d+\.\d+>', '', segment)
        segment = re.sub(r'<c>(.*?)</c>', r'\1', segment)
        segment = re.sub(r'&gt;', '>', segment)
        
        # Remove audio cues and sound descriptions
        segment = remove_audio_cues(segment)
        
        # Get clean text
        clean_text = ' '.join([line.strip() for line in segment.split('\n') if line.strip()])
        if clean_text:
            clean_texts.append(clean_text)
    
    # Join all segments and normalize whitespace
    full_text = ' '.join(clean_texts)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    
    # Final audio cue cleanup
    full_text = remove_audio_cues(full_text)
    
    # Remove repetitive phrases (phrases that repeat 3+ words)
    cleaned_text = remove_repetitive_phrases(full_text)
    
    return cleaned_text

def clean_plain_text(content):
    """Clean plain text content by removing audio cues and normalizing."""
    # Remove audio cues and sound descriptions
    content = remove_audio_cues(content)
    
    # Remove repetitive phrases
    cleaned_content = remove_repetitive_phrases(content)
    
    return cleaned_content

def remove_repetitive_phrases(text, min_phrase_length=3):
    """Remove repetitive phrases from text using a more robust algorithm."""
    words = text.split()
    result = []
    i = 0
    
    while i < len(words):
        # Skip if we're at the end
        if i + min_phrase_length >= len(words):
            result.extend(words[i:])
            break
        
        # Try different phrase lengths to find the longest repeating pattern
        best_phrase_length = 0
        best_repetitions = 0
        
        for phrase_len in range(min_phrase_length, min(15, len(words) - i)):
            if i + phrase_len >= len(words):
                break
                
            phrase = words[i:i+phrase_len]
            phrase_str = ' '.join(phrase)
            
            # Count consecutive repetitions
            repetitions = 0
            pos = i
            while pos + phrase_len <= len(words) and ' '.join(words[pos:pos+phrase_len]) == phrase_str:
                repetitions += 1
                pos += phrase_len
            
            # If we found repetitions and this is the longest pattern so far
            if repetitions > 1 and phrase_len > best_phrase_length:
                best_phrase_length = phrase_len
                best_repetitions = repetitions
        
        if best_phrase_length > 0 and best_repetitions > 1:
            # Add the phrase once and skip all repetitions
            result.extend(words[i:i+best_phrase_length])
            i += best_phrase_length * best_repetitions
        else:
            # No repetition found, add current word and move forward
            result.append(words[i])
            i += 1
    
    # Additional cleanup: remove duplicate sentences
    text_result = ' '.join(result)
    sentences = re.split(r'[.!?]+', text_result)
    unique_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and sentence not in unique_sentences:
            unique_sentences.append(sentence)
    
    return '. '.join(unique_sentences) + '.' if unique_sentences else ''

def format_text_chinese(text, words_per_chunk=100, chars_per_line=50):
    """Format Chinese text with approximately 50 characters per line."""
    # Clean up the text but preserve basic structure
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    
    chunks = []
    
    # Divide into chunks based on character count (approximate)
    chunk_size = words_per_chunk * 6  # Approximate characters per chunk for Chinese
    
    for i in range(0, len(text), chunk_size):
        chunk_text = text[i:i + chunk_size]
        
        # Format each chunk with chars_per_line characters per line
        formatted_lines = []
        
        for j in range(0, len(chunk_text), chars_per_line):
            line_text = chunk_text[j:j + chars_per_line]
            if line_text.strip():
                formatted_lines.append(line_text.strip())
        
        if formatted_lines:
            chunks.append('\n'.join(formatted_lines))
    
    return '\n\n'.join(chunks)

def format_text_english(text, words_per_chunk=100, words_per_line=15):
    """Format English text with existing rules (15 words per line)."""
    words = text.split()
    chunks = []
    
    # Divide into chunks of words_per_chunk
    for i in range(0, len(words), words_per_chunk):
        chunk_words = words[i:i+words_per_chunk]
        
        # Format each chunk with words_per_line words per line
        formatted_lines = []
        for j in range(0, len(chunk_words), words_per_line):
            line_words = chunk_words[j:j+words_per_line]
            formatted_lines.append(' '.join(line_words))
        
        chunks.append('\n'.join(formatted_lines))
    
    return '\n\n'.join(chunks)

def format_text(text, words_per_chunk=100, words_per_line=15):
    """Format text based on detected language."""
    language = detect_language(text)
    
    if language == 'chinese':
        return format_text_chinese(text, words_per_chunk=500, chars_per_line=50)
    else:
        return format_text_english(text, words_per_chunk, words_per_line)

def process_file(input_file, output_file=None, words_per_chunk=100):
    """Process a single transcript file."""
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        return False
    
    # Read the file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Clean the content based on file type
    if input_file.endswith('.vtt'):
        cleaned_content = clean_vtt_content(content)
    else:
        # For plain text files, apply audio cue removal and basic cleaning
        cleaned_content = clean_plain_text(content.strip())
    
    # Format the text based on detected language
    formatted_text = format_text(cleaned_content, words_per_chunk)
    
    # Create output directory if it doesn't exist
    if output_file is None:
        output_file = os.path.join(os.path.dirname(input_file), f"{os.path.splitext(os.path.basename(input_file))[0]}_clean.txt")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(formatted_text)
    
    print(f"Processed transcript saved to: {output_file}")
    return True

def process_directory(input_dir, output_dir, words_per_chunk=100, words_per_line=15):
    """Process all VTT files in a directory."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all VTT files
    vtt_files = glob.glob(os.path.join(input_dir, "*.vtt"))
    
    if not vtt_files:
        print(f"No VTT files found in {input_dir}")
        return False
    
    # Process each file
    for vtt_file in vtt_files:
        base_name = os.path.basename(vtt_file)
        output_file = os.path.join(output_dir, f"{os.path.splitext(base_name)[0]}_clean.txt")
        process_file(vtt_file, output_file, words_per_chunk, words_per_line)
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use command line arguments if provided
        input_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        words_per_chunk = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        words_per_line = int(sys.argv[4]) if len(sys.argv) > 4 else 15
        
        if os.path.isdir(input_path):
            # Process directory
            if not output_path:
                output_path = os.path.join(os.path.dirname(input_path), "clean")
            process_directory(input_path, output_path, words_per_chunk, words_per_line)
        else:
            # Process single file
            if not output_path:
                output_path = os.path.join(os.path.dirname(input_path), f"{os.path.splitext(os.path.basename(input_path))[0]}_clean.txt")
            process_file(input_path, output_path, words_per_chunk)
    else:
        # Use default paths
        transcript_dir = "/Users/wenqingli/Documents/repo/audio classifier/transcript/process"
        output_dir = "/Users/wenqingli/Documents/repo/audio classifier/transcript/clean"
        
        # Check if process directory exists
        if not os.path.exists(transcript_dir):
            # Create it if it doesn't exist
            os.makedirs(transcript_dir, exist_ok=True)
            print(f"Created directory: {transcript_dir}")
            print("Please place VTT files in this directory and run the script again.")
        else:
            process_directory(transcript_dir, output_dir)
