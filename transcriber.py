import os
import tempfile
import math
import speech_recognition as sr
from pydub import AudioSegment
import imageio_ffmpeg

# Set ffmpeg executable path dynamically from imageio_ffmpeg
AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

# Default candidate languages to probe when Auto-Detect is active
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

    def convert_to_wav(self, input_path: str) -> str:
        """
        Converts any supported audio file to a temporary mono 16kHz PCM WAV file.
        Original file remains completely untouched.
        """
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav_path = temp_wav.name
        temp_wav.close()
        
        audio.export(temp_wav_path, format="wav")
        return temp_wav_path

    def detect_language(self, wav_path: str) -> str:
        """
        Language Auto-Detection Strategy:
        Probes the first ~12 seconds of audio against top candidate languages using
        Google Speech Recognition API with show_all=True. Evaluates the highest confidence
        score and returned hypotheses to pick the most accurate language automatically.
        """
        audio_segment = AudioSegment.from_file(wav_path)
        sample_duration_ms = min(len(audio_segment), 12000)
        sample_audio = audio_segment[:sample_duration_ms]
        
        temp_sample = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_sample_path = temp_sample.name
        temp_sample.close()
        
        sample_audio.export(temp_sample_path, format="wav")
        
        best_lang = "he-IL"  # default fallback
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
        Converts the audio file to standard WAV, chunks it into ~35s segments to bypass
        Google API single-request limits, transcribes each chunk, and returns full text.
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

            audio = AudioSegment.from_file(temp_wav_path)
            chunk_length_ms = 35000  # 35 seconds chunking
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
                    pass  # Silence or unrecognizable chunk
                except sr.RequestError as e:
                    raise RuntimeError(f"שגיאת תקשורת מול Google Speech API: {e}")
                finally:
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                        
                if progress_callback:
                    progress_callback(f"מתמלל מקטע {i+1} מתוך {total_chunks} ({selected_lang})...")

            return " ".join(full_transcript_parts).strip()

        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
