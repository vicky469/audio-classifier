#!/usr/bin/env python3
"""
Simple transcript processor that:
1. Cleans VTT files and plain text files
2. Formats text based on detected language
"""

import os
import re
import sys
import json

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
    """Detect if text is primarily Chinese or English (fallback only)."""
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

def format_text(text, language, words_per_chunk=100, words_per_line=20):
    """Format text based on provided language from metadata."""
    
    if language == 'zh':
        # For Chinese: use character-based chunking
        words_per_chunk = 500
        words_per_line = 50
        
        chunks = []
        # Split text into chunks of exactly words_per_chunk characters (including spaces)
        for i in range(0, len(text), words_per_chunk):
            chunk_text = text[i:i + words_per_chunk]
            
            # Add line breaks within each chunk based on words_per_line
            formatted_lines = []
            for j in range(0, len(chunk_text), words_per_line):
                line_text = chunk_text[j:j + words_per_line]
                formatted_lines.append(line_text)
            
            chunks.append('\n'.join(formatted_lines))
        
        return '\n\n'.join(chunks)
    
    else:
        # For English: use word-based chunking
        words = text.split()
        chunks = []
        
        # Split into chunks of words_per_chunk words
        for i in range(0, len(words), words_per_chunk):
            chunk_words = words[i:i + words_per_chunk]
            
            # Add line breaks within each chunk based on words_per_line
            formatted_lines = []
            for j in range(0, len(chunk_words), words_per_line):
                line_words = chunk_words[j:j + words_per_line]
                line_text = ' '.join(line_words)
                formatted_lines.append(line_text)
            
            chunks.append('\n'.join(formatted_lines))
        
        return '\n\n'.join(chunks)

def get_language_from_metadata(input_file):
    """Get language from metadata JSON file based on input file."""
    # Get the base name without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Look for metadata JSON in the same directory
    input_dir = os.path.dirname(input_file)
    metadata_file = os.path.join(input_dir, f"{base_name}.json")
    
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            language = metadata.get('language')
            if language:
                return language
            else:
                print(f"Warning: No language found in {metadata_file}, defaulting to English")
                return 'en'
        except Exception as e:
            print(f"Warning: Could not read metadata from {metadata_file}: {e}")
            return 'en'
    else:
        print(f"Warning: No metadata file found at {metadata_file}, defaulting to English")
        return 'en'

def process_file(input_file, output_file=None):
    """Process a single transcript file."""
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        return False
    
    # Get language from metadata
    language = get_language_from_metadata(input_file)
    
    print(f"Processing {input_file} with language: {language}")
    
    # Read the file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Clean the content based on file type
    if input_file.endswith('.vtt'):
        cleaned_content = clean_vtt_content(content)
    else:
        cleaned_content = clean_plain_text(content.strip())
    
    # Format the text using language from metadata
    formatted_text = format_text(cleaned_content, language=language)
    
    # Create output directory if it doesn't exist
    if output_file is None:
        output_file = os.path.join(os.path.dirname(input_file), f"{os.path.splitext(os.path.basename(input_file))[0]}_clean.txt")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(formatted_text)
    
    print(f"Processed transcript saved to: {output_file}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcript_processor.py <input_file> [output_file]")
        print("Example: python transcript_processor.py transcript.vtt clean.txt")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    
    if not os.path.exists(input_path):
        print(f"Error: File {input_path} not found")
        sys.exit(1)
    
    # Process single file
    if not output_path:
        output_path = os.path.join(os.path.dirname(input_path), f"{os.path.splitext(os.path.basename(input_path))[0]}_clean.txt")
    
    success = process_file(input_path, output_path)
    
    if not success:
        sys.exit(1)
