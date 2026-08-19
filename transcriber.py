import os
import tempfile
import math
import subprocess
import speech_recognition as sr
from pydub import AudioSegment
import imageio_ffmpeg

# Candidate languages to probe when Auto-Detect is active
CANDIDATE_LANGUAGES = [
    ("he-IL", "עברית"),
    ("en-US", "English"),
    ("ar-IL", "العربية"),
    ("ru-RU", "Русский"),
    ("fr-FR", "Français"),
    ("es-ES", "Español")
]


class AudioTranscriber:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    def convert_to_wav(self, input_path: str) -> str:
        """
        Directly converts ANY audio format (MP3, M4A, AAC, OGG, AMR, FLAC, etc.) 
        to a temporary mono 16kHz PCM WAV file using bundled FFmpeg executable.
        Bypasses ffprobe entirely to prevent [WinError 2].
        """
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav_path = temp_wav.name
        temp_wav.close()

        # Hide console window on Windows during subprocess execution
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.CREATE_NO_WINDOW

        cmd = [
            self.ffmpeg_exe,
            "-y",               # Overwrite output
            "-loglevel", "error", # Suppress verbose output
            "-i", input_path,   # Input file
            "-vn",              # Disable video
            "-acodec", "pcm_s16le", # Standard 16-bit PCM
            "-ac", "1",         # Mono channel
            "-ar", "16000",     # 16kHz sample rate
            temp_wav_path
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags,
                check=True
            )
        except subprocess.CalledProcessError as e:
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
            err_msg = e.stderr.decode("utf-8", errors="ignore")
            raise RuntimeError(f"שגיאה בהמרת קובץ השמע: {err_msg}")

        return temp_wav_path

    def detect_language(self, wav_path: str) -> str:
        """
        Probes the first ~12 seconds of the converted audio against candidate languages 
        using Google Speech Recognition API to select the best match automatically.
        """
        audio_segment = AudioSegment.from_file(wav_path, format="wav")
        sample_duration_ms = min(len(audio_segment), 12000)
        sample_audio = audio_segment[:sample_duration_ms]
        
        temp_sample = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_sample_path = temp_sample.name
        temp_sample.close()
        
        sample_audio.export(temp_sample_path, format="wav")
        
        best_lang = "he-IL"  # Fallback
        best_score = -1.0
        
        try:
            with sr.AudioFile(temp_sample_path) as source:
                audio_data = self.recognizer.record(source)
                
            for lang_code, _ in CANDIDATE_LANGUAGES:
                try:
                    response = self.recognizer.recognize_google(
                        audio_data, language=lang_code, show_all=True
                    )
                    if isinstance(response, dict) and "alternative" in response:
                        alternatives = response["alternative"]
                        if alternatives:
                            top_alt = alternatives[0]
                            confidence = top_alt.get("confidence", 0.75)
                            transcript = top_alt.get("transcript", "")
                            score = confidence * (len(transcript.split()) + 1)
                            if score > best_score:
                                best_score = score
                                best_lang = lang_code
                except Exception:
                    continue
        finally:
            if os.path.exists(temp_sample_path):
                os.remove(temp_sample_path)
                
        return best_lang

    def transcribe_audio_file(self, file_path: str, language_code: str = "auto", progress_callback=None) -> str:
        """
        Converts audio to standard WAV, chunks it to prevent timeouts,
        transcribes each segment via Google API, and returns full text.
        """
        temp_wav_path = None
        full_transcript_parts = []
        
        try:
            temp_wav_path = self.convert_to_wav(file_path)
            
            selected_lang = language_code
            if language_code == "auto":
                if progress_callback:
                    progress_callback("מזהה שפת דיבור אוטומטית...")
                selected_lang = self.detect_language(temp_wav_path)

            audio = AudioSegment.from_file(temp_wav_path, format="wav")
            chunk_length_ms = 35000  # 35 seconds per chunk
            total_chunks = math.ceil(len(audio) / chunk_length_ms)
            
            if total_chunks == 0:
                return ""

            for i in range(total_chunks):
                start_ms = i * chunk_length_ms
                end_ms = min((i + 1) * chunk_length_ms, len(audio))
                chunk = audio[start_ms:end_ms]
                
                chunk_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                chunk_path = chunk_file.name
                chunk_file.close()
                
                try:
                    chunk.export(chunk_path, format="wav")
                    with sr.AudioFile(chunk_path) as source:
                        audio_data = self.recognizer.record(source)
                    
                    text = self.recognizer.recognize_google(audio_data, language=selected_lang)
                    if text:
                        full_transcript_parts.append(text.strip())
                except sr.UnknownValueError:
                    pass  # No speech detected in this chunk
                except sr.RequestError as e:
                    raise RuntimeError(f"שגיאת תקשורת מול Google API: {e}")
                finally:
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                        
                if progress_callback:
                    progress_callback(f"מתמלל מקטע {i+1} מתוך {total_chunks} ({selected_lang})...")

            return " ".join(full_transcript_parts).strip()

        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
