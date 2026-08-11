import os
import sys
import subprocess
import threading
from typing import Callable, Optional

class GeminiClient:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self._is_running = False

    def _get_executable_path(self) -> str:
        """מאתר את הנתיב ל-Gemini CLI, בין אם הורץ מקוד מקור ובין אם ארוז ב-EXE."""
        if getattr(sys, 'frozen', False):
            # בזמן ריצה מתוך PyInstaller
            base_path = sys._MEIPASS
            # נתיב לקובץ ההפעלה הארוז של Gemini CLI/Node
            bundled_gemini = os.path.join(base_path, "gemini-cli", "gemini.exe")
            if os.path.exists(bundled_gemini):
                return bundled_gemini
            return os.path.join(base_path, "gemini")
        # בזמן פיתוח
        return "npx @google/generative-ai-cli"

    def run_prompt_async(self, prompt: str, api_key: str, on_data: Callable[[str], None], on_complete: Callable[[int], None]):
        """מריץ את הפקודה באופן אסינכרוני כדי לא לחסום את הממשק."""
        def worker():
            self._is_running = True
            env = os.environ.copy()
            if api_key:
                env["GEMINI_API_KEY"] = api_key

            cmd = f"{self._get_executable_path()} \"{prompt}\""
            
            try:
                self.process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    encoding='utf-8',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                while True:
                    line = self.process.stdout.readline()
                    if not line and self.process.poll() is not None:
                        break
                    if line:
                        on_data(line)

                stderr_out = self.process.stderr.read()
                if stderr_out:
                    on_data(f"\n[Error/Warning]: {stderr_out}")

                return_code = self.process.poll() or 0
                on_complete(return_code)

            except Exception as e:
                on_data(f"\n[System Error]: {str(e)}")
                on_complete(-1)
            finally:
                self._is_running = False
                self.process = None

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def stop(self):
        """עוצר את התהליך הרץ."""
        if self.process and self._is_running:
            self.process.terminate()
            self._is_running = False
