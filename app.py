import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
from gemini_client import GeminiClient

class GeminiGUIApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Gemini CLI Desktop")
        self.root.geometry("800x650")
        self.root.minsize(600, 450)

        self.client = GeminiClient()

        self._setup_ui()

    def _setup_ui(self):
        # API Key Frame
        key_frame = ttk.LabelFrame(self.root, text="הגדרות אבטחה", padding=10)
        key_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(key_frame, text="GEMINI_API_KEY:").pack(side=tk.LEFT, padx=5)
        self.api_key_entry = ttk.Entry(key_frame, show="*", width=40)
        self.api_key_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # טעינת מפתח מסביבת העבודה אם קיים
        if "GEMINI_API_KEY" in os.environ:
            self.api_key_entry.insert(0, os.environ["GEMINI_API_KEY"])

        # Chat display area
        display_frame = ttk.Frame(self.root, padding=10)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.chat_display = scrolledtext.ScrolledText(display_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 10))
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Status Bar
        self.status_var = tk.StringVar(value="מוכן לפעולה")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

        # Input Frame
        input_frame = ttk.Frame(self.root, padding=10)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

        self.prompt_entry = ttk.Entry(input_frame, font=("Segoe UI", 10))
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.prompt_entry.bind("<Return>", lambda e: self.send_prompt())

        self.send_btn = ttk.Button(input_frame, text="שלח", command=self.send_prompt)
        self.send_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(input_frame, text="עצור", command=self.stop_execution, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        self.clear_btn = ttk.Button(input_frame, text="נקה", command=self.clear_chat)
        self.clear_btn.pack(side=tk.LEFT, padx=2)

    def append_chat(self, text: str):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, text)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def send_prompt(self):
        prompt = self.prompt_entry.get().strip()
        api_key = self.api_key_entry.get().strip()

        if not prompt:
            return

        if not api_key:
            messagebox.showwarning("שגיאה", "אנא הזן GEMINI_API_KEY תקין לפני שליחת הבקשה.")
            return

        self.prompt_entry.delete(0, tk.END)
        self.append_chat(f"\n\n--- You ---\n{prompt}\n\n--- Gemini ---\n")
        
        self.send_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Gemini מעבד את הבקשה...")

        def on_data(data: str):
            self.root.after(0, self.append_chat, data)

        def on_complete(code: int):
            def update():
                self.send_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                if code == 0:
                    self.status_var.set("הושלם בהצלחה")
                else:
                    self.status_var.set(f"התהליך הסתיים עם קוד שגיאה: {code}")
            self.root.after(0, update)

        self.client.run_prompt_async(prompt, api_key, on_data, on_complete)

    def stop_execution(self):
        self.client.stop()
        self.status_var.set("הפעולה הופסקה על ידי המשתמש")
        self.send_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def clear_chat(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = GeminiGUIApp(root)
    root.mainloop()
