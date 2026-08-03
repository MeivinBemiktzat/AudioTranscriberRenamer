```python
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

BASE = Path(__file__).resolve().parent
ENGINES = BASE / "engines"

class AIStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Studio")
        self.root.geometry("1000x700")
        self.root.minsize(850, 600)
        self.root.configure(bg="#0f172a")

        self.model = None
        self.process = None

        self.build_ui()

    def build_ui(self):
        header = tk.Frame(self.root, bg="#0f172a")
        header.pack(fill="x", padx=30, pady=25)

        tk.Label(
            header,
            text="AI Studio",
            bg="#0f172a",
            fg="white",
            font=("Segoe UI", 28, "bold")
        ).pack(anchor="e")

        tk.Label(
            header,
            text="הרצת מודלי AI מקומיים",
            bg="#0f172a",
            fg="#94a3b8",
            font=("Segoe UI", 12)
        ).pack(anchor="e")

        main = tk.Frame(self.root, bg="#172033")
        main.pack(fill="both", expand=True, padx=30, pady=10)

        sidebar = tk.Frame(main, bg="#172033", width=280)
        sidebar.pack(side="right", fill="y", padx=20, pady=20)

        tk.Label(
            sidebar,
            text="בחירת מודל",
            bg="#172033",
            fg="white",
            font=("Segoe UI", 17, "bold")
        ).pack(anchor="e", pady=(0, 15))

        tk.Button(
            sidebar,
            text="📁  בחר קובץ GGUF",
            command=self.select_model,
            bg="#7c3aed",
            fg="white",
            activebackground="#6d28d9",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=12,
            cursor="hand2"
        ).pack(fill="x")

        self.model_name = tk.Label(
            sidebar,
            text="לא נבחר מודל",
            bg="#172033",
            fg="#e2e8f0",
            wraplength=250,
            justify="right",
            font=("Segoe UI", 10)
        )
        self.model_name.pack(anchor="e", pady=20)

        self.model_type = tk.Label(
            sidebar,
            text="סוג: —",
            bg="#172033",
            fg="#94a3b8",
            font=("Segoe UI", 10)
        )
        self.model_type.pack(anchor="e")

        self.run_button = tk.Button(
            sidebar,
            text="▶  הרץ מודל",
            command=self.run_model,
            state="disabled",
            bg="#334155",
            fg="white",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            pady=11
        )
        self.run_button.pack(fill="x", pady=(30, 8))

        tk.Button(
            sidebar,
            text="■  עצור",
            command=self.stop_model,
            bg="#334155",
            fg="white",
            relief="flat",
            font=("Segoe UI", 10),
            pady=10
        ).pack(fill="x")

        content = tk.Frame(main, bg="#172033")
        content.pack(side="left", fill="both", expand=True, padx=(0, 20), pady=20)

        tk.Label(
            content,
            text="פרומפט",
            bg="#172033",
            fg="white",
            font=("Segoe UI", 17, "bold")
        ).pack(anchor="e")

        self.prompt = tk.Text(
            content,
            height=7,
            bg="#0b1220",
            fg="white",
            insertbackground="white",
            relief="flat",
            wrap="word",
            font=("Segoe UI", 11)
        )
        self.prompt.pack(fill="x", pady=12)

        tk.Label(
            content,
            text="פלט",
            bg="#172033",
            fg="white",
            font=("Segoe UI", 17, "bold")
        ).pack(anchor="e", pady=(10, 0))

        self.output = scrolledtext.ScrolledText(
            content,
            bg="#0b1220",
            fg="#dbeafe",
            insertbackground="white",
            relief="flat",
            wrap="word",
            font=("Consolas", 10)
        )
        self.output.pack(fill="both", expand=True, pady=12)

        self.status = tk.Label(
            self.root,
            text="מוכן",
            bg="#0b1220",
            fg="#94a3b8",
            anchor="e",
            padx=30,
            pady=8,
            font=("Segoe UI", 9)
        )
        self.status.pack(fill="x")

    def select_model(self):
        filename = filedialog.askopenfilename(
            title="בחר מודל GGUF",
            filetypes=[
                ("מודלי GGUF", "*.gguf"),
                ("כל הקבצים", "*.*")
            ]
        )

        if not filename:
            return

        self.model = Path(filename)
        name = self.model.name.lower()

        if "stable-diffusion" in name:
            model_type = "Stable Diffusion — תמונה"
        elif "ltx" in name:
            model_type = "LTX-Video — וידאו"
        elif "yue" in name:
            model_type = "YuE — מוזיקה"
        elif "llama" in name or "mesh" in name:
            model_type = "LLaMA / GGUF — טקסט"
        else:
            model_type = "GGUF — לא זוהה"

        self.model_name.config(text=self.model.name)
        self.model_type.config(text="סוג: " + model_type)
        self.run_button.config(state="normal")
        self.status.config(text="המודל נבחר — מוכן")

    def run_model(self):
        if not self.model:
            return

        name = self.model.name.lower()
        prompt = self.prompt.get("1.0", "end").strip()

        if not prompt:
            prompt = "שלום! ענה בעברית."

        if "llama" in name or "mesh" in name:
            executable = ENGINES / "llama-cli.exe"

            if not executable.exists():
                messagebox.showerror(
                    "מנוע חסר",
                    "לא נמצא llama-cli.exe בתוך תיקיית engines."
                )
                return

            command = [
                str(executable),
                "-m",
                str(self.model),
                "-p",
                prompt,
                "-n",
                "512"
            ]

        elif "stable-diffusion" in name:
            executable = ENGINES / "sd-cli.exe"

            if not executable.exists():
                messagebox.showerror(
                    "מנוע חסר",
                    "לא נמצא sd-cli.exe בתוך תיקיית engines."
                )
                return

            output_file = BASE / "output.png"

            command = [
                str(executable),
                "-m",
                str(self.model),
                "-p",
                prompt,
                "-o",
                str(output_file)
            ]

        elif "ltx" in name:
            messagebox.showinfo(
                "LTX-Video",
                "LTX-Video זוהה, אך עדיין לא חובר מנוע ההרצה שלו."
            )
            return

        elif "yue" in name:
            messagebox.showinfo(
                "YuE",
                "YuE זוהה, אך עדיין לא חובר מנוע ההרצה שלו."
            )
            return

        else:
            messagebox.showwarning(
                "מודל לא מזוהה",
                "לא נמצא מנוע מתאים לקובץ הזה."
            )
            return

        self.output.delete("1.0", "end")
        self.status.config(text="מריץ מודל...")
        self.run_button.config(state="disabled")

        def worker():
            try:
                self.process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )

                for line in self.process.stdout:
                    self.root.after(
                        0,
                        lambda x=line: self.write_output(x)
                    )

                code = self.process.wait()

                self.root.after(
                    0,
                    lambda: self.status.config(
                        text=f"ההרצה הסתיימה — קוד {code}"
                    )
                )

            except Exception as error:
                self.root.after(
                    0,
                    lambda: self.write_output(
                        f"\nשגיאה: {error}\n"
                    )
                )

            finally:
                self.process = None
                self.root.after(
                    0,
                    lambda: self.run_button.config(state="normal")
                )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def write_output(self, text):
        self.output.insert("end", text)
        self.output.see("end")

    def stop_model(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.status.config(text="ההרצה נעצרה")


if __name__ == "__main__":
    root = tk.Tk()
    app = AIStudio(root)
    root.mainloop()
```
