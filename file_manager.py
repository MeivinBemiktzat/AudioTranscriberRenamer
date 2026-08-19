import os
import re
from typing import List, Dict

SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".aac", ".ogg", 
    ".opus", ".flac", ".wma", ".amr", ".3gp"
}

INVALID_FILENAME_CHARS = r'[\\/*?:"<>|]'


def sanitize_filename(name: str) -> str:
    """Removes illegal Windows filename characters and trims whitespace."""
    clean = re.sub(INVALID_FILENAME_CHARS, '', name)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip(" .")


def generate_short_title(transcript: str, word_count: int = 6) -> str:
    """Extracts the first N words of a transcript for the new filename."""
    if not transcript:
        return "ללא_תמלול"
    words = transcript.strip().split()
    chosen_words = words[:max(1, word_count)]
    title = " ".join(chosen_words)
    sanitized = sanitize_filename(title)
    return sanitized if sanitized else "הקלטה_מתומללת"


def get_unique_filepath(directory: str, base_name: str, extension: str) -> str:
    """
    Returns a unique file path in the directory.
    If 'base_name.ext' already exists, generates 'base_name (2).ext', 'base_name (3).ext', etc.
    """
    candidate_name = f"{base_name}{extension}"
    candidate_path = os.path.join(directory, candidate_name)
    
    if not os.path.exists(candidate_path):
        return candidate_path
        
    counter = 2
    while True:
        candidate_name = f"{base_name} ({counter}){extension}"
        candidate_path = os.path.join(directory, candidate_name)
        if not os.path.exists(candidate_path):
            return candidate_path
        counter += 1


def scan_audio_files(folder_path: str, skip_processed: bool = False) -> List[str]:
    """Scans the directory for supported audio files."""
    if not os.path.isdir(folder_path):
        return []
    
    results = []
    for item in sorted(os.listdir(folder_path)):
        full_path = os.path.join(folder_path, item)
        if os.path.isfile(full_path):
            _, ext = os.path.splitext(item)
            if ext.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                if skip_processed:
                    # If TXT with same base name already exists, consider it processed
                    base, _ = os.path.splitext(full_path)
                    if os.path.exists(f"{base}.txt"):
                        continue
                results.append(full_path)
    return results


def save_transcript_to_txt(audio_path: str, transcript: str) -> str:
    """Saves the full transcript to a UTF-8 encoded .txt file next to the audio file."""
    base, _ = os.path.splitext(audio_path)
    txt_path = f"{base}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    return txt_path


def apply_file_renames(preview_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Executes actual file renaming on disk based on the confirmed preview items.
    """
    results = []
    for item in preview_items:
        original_path = item.get("original_path")
        target_path = item.get("target_path")
        status = item.get("status")
        
        if status != "מוכן לשינוי" or not original_path or not target_path:
            results.append({**item, "final_status": "דולג"})
            continue
            
        try:
            if original_path == target_path:
                results.append({**item, "final_status": "ללא שינוי"})
                continue
                
            os.rename(original_path, target_path)
            
            # If a transcript text file was created with the old name, rename it too
            old_txt = os.path.splitext(original_path)[0] + ".txt"
            new_txt = os.path.splitext(target_path)[0] + ".txt"
            if os.path.exists(old_txt):
                if not os.path.exists(new_txt):
                    os.rename(old_txt, new_txt)

            results.append({**item, "final_status": "השם שונה בהצלחה"})
        except Exception as e:
            results.append({**item, "final_status": f"שגיאה בשינוי שם: {e}"})
            
    return results
